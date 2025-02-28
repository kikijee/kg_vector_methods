import glob
from ..config import settings
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import TokenTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain.schema import Document
from openai import OpenAI
from langchain.schema import Document
import glob
from langchain.text_splitter import CharacterTextSplitter
from typing import List
import os
from string import Template
import glob
import os
from langchain.docstore.document import Document
from langchain.text_splitter import TokenTextSplitter
from neo4j import GraphDatabase
from pydantic import BaseModel
import json
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate
)
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains import RetrievalQAWithSourcesChain

from ..utils import data_retrieval_util
import logging
import traceback

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class Entity(BaseModel):
    label: str 
    id: str 

class EntityResponse(BaseModel):
    entities: List[Entity]


def define_chunks():
    try:
        # # Get all text files in the directory
        # raw_files = glob.glob(r"./app/data/*.txt")

        # List to store chunked files separately
        chunked_files_list = []

        # Chunking strategy: Each chunk will have at most 1000 characters
        # 20 characters will overlap between chunks to add context
        text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=20)

        files = data_retrieval_util.fetch_files()

        for file in files:

            file_name = file["metadata"]["file_name"]
            document = Document(page_content=file["page_content"], metadata={"file_name": file_name})
            
            # Chunk the document into smaller pieces
            chunked_documents = text_splitter.split_documents([document])

            # Create chunked files list with unique chunk IDs and page content
            chunked_files = [
                {
                    "id": f"{file_name}_chunk_{index}",  # Unique chunk ID
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                }
                for index, doc in enumerate(chunked_documents)
            ]

            # Add the chunked files for the current document into the list
            chunked_files_list.append(chunked_files)

        return chunked_files_list

    except Exception as e:
        logger.error(f"Error in define_chunks(): {traceback.format_exc()}")
        raise RuntimeError("Error processing text chunks") from e


    
def embed_data(data):
    try:
        embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key
        )

        for file in data:
            for chunk in file:
                # Get the chunk's page content
                page_content = chunk["page_content"]
                # Use the embedding model to create a vector (embedding) for the text
                chunk["vector"] = embeddings.embed_query(page_content)
    except Exception as e:
        logger.error(f"Error in embed_data(): {traceback.format_exc()}")
        raise RuntimeError("Error embedding data") from e

    
def create_index_for_vector(driver):
    try:
        # Create an index for the vector property on Chunk nodes
        with driver.session() as session:
            session.run("""
                CREATE VECTOR INDEX Transcript IF NOT EXISTS
                FOR (n:Chunk) ON (n.vector) 
                OPTIONS {
                    indexProvider: 'vector-2.0',
                    indexConfig: {
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }
                };
            """)
        print("Index for 'vector' created successfully.")
    except Exception as e:
        logger.error(f"Error in create_index_for_vector(): {traceback.format_exc()}")
        raise RuntimeError("Error creating index for vector value") from e
    
def extract_entities_from_text(text: str):
    client = OpenAI(api_key= settings.openai_api_key)
    prompt_template = """
    From the Project Brief below, extract the following Entities & relationships described in the mentioned format 
    0. ALWAYS FINISH THE OUTPUT. Never send partial responses
    1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
    `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Objective',id:string; //Objective that is mentioned in the text; `id` property is one word that summarizes the objective as a whole. If there is a space please use an underscore instead. This one word must only be in lowercase;
    label:'Challenge',id:string,text:string; //Challenges that are talked about; `id` property is one word that summarizes the challange as a whole. If there is a space please use an underscore instead. This one word must only be in lowercase;
    label: 'Tool', id:string; //Please gather ALL the tools that are talked about; `id` property is the specific tool name. If there is a space please use an underscore instead. This id should be in lowercase; 
    Note: There can possibly be multiple challenges and objectives mentioned in one chunk of text limit 2 `Challenge`s and 2 `Objective`s per chunk


    3. The output should look like :
    {
        "entities": [{"label": "Objective","id":"unit_testing"}]
    }

    or 

    {
        "entities": []
    }

    if there are no found entities

    Case Sheet:
    $ctext
     """
    
    prompt = Template(prompt_template).substitute(ctext = text)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Use a valid model
            messages=[
                {"role": "system", "content": "You are an expert in graph representations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2024,  # Limit response length
            response_format=EntityResponse
        )

        response_content = response.choices[0].message.content
        if not response_content:
            print("Empty response from API.")
            return {"entities": []}
        
        res = json.loads(response.choices[0].message.content)  # Parse JSON safely
        print(res)
        return res
    except Exception as e:
        logger.error(f"Error in extract_entities_from_text(): {traceback.format_exc()}")
        raise RuntimeError("Error extracting entities from text") from e


def insert_data(data):
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        create_index_for_vector(driver)
        # Define the Cypher query for inserting documents and chunks
        import_query = """
        UNWIND $data AS file_data
        MERGE (doc:Document {id: file_data.file_name})
        ON CREATE SET doc.created_at = datetime()

        FOREACH (chunk IN file_data.chunks |
            MERGE (c:Chunk {id: chunk.id}) 
            ON CREATE SET c.page_content = chunk.page_content,
                        c.vector = chunk.vector,
                        c.created_at = datetime()
            MERGE (doc)-[:HAS_CHUNK]->(c)
            
            FOREACH (entity IN chunk.entities |
                FOREACH (_ IN CASE WHEN entity.label = "Challenge" THEN [1] ELSE [] END |
                    MERGE (e:Challenge {id: entity.id})
                    MERGE (c)-[:MENTIONS]->(e)
                )
                FOREACH (_ IN CASE WHEN entity.label = "Objective" THEN [1] ELSE [] END |
                    MERGE (e:Objective {id: entity.id})
                    MERGE (c)-[:MENTIONS]->(e)
                )
                FOREACH (_ IN CASE WHEN entity.label = "Tool" THEN [1] ELSE [] END |
                    MERGE (e:Tool {id: entity.id})
                    MERGE (c)-[:MENTIONS]->(e)
                )
            )
        )
        """
        transformed_data = []
        for file_chunks in data:  
            if not file_chunks:
                continue  # Skip empty files
            
            file_name = file_chunks[0]["metadata"]["file_name"]

            for chunk in file_chunks:
                # Extract entities from chunk text (assuming chunk["page_content"] contains the text)
                entities = extract_entities_from_text(chunk["page_content"])['entities']
                chunk["entities"] = entities

            transformed_data.append({
                "file_name": file_name,
                "chunks": [
                    {
                        "id": f"{chunk["id"]}",
                        "page_content": chunk["page_content"],
                        "metadata": chunk["metadata"],
                        "vector": chunk["vector"],
                        "entities": chunk.get("entities", [])
                    } 
                    for chunk in file_chunks
                ]
            })


        
        # Execute the query
        with driver.session() as session:
            for i in transformed_data:
                session.run(import_query, data=i)

        return transformed_data

    except Exception as e:
        logger.error(f"Error in insert_data(): {traceback.format_exc()}")
        raise RuntimeError("Error inserting data into neo4j") from e

    

def generate_graph ():
    try:
        data = define_chunks()
        embed_data(data)
        transformed = insert_data(data)
        return{
            "message": "success",
            "data": transformed
        }
    except RuntimeError as e:
        logger.error(f"Runtime error in generate_graph(): {traceback.format_exc()}")
        raise

    except Exception as e:
        logger.critical(f"Unexpected error in generate_graph(): {traceback.format_exc()}")
        raise RuntimeError("Unexpected error while generating graph") from e
    
def perform_search(query: str, k: int = 1):
    try:
        # Initialize the vector store
        embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        client = OpenAI(api_key= settings.openai_api_key)

        neo4j_db = Neo4jVector.from_existing_index(
            embedding=embeddings,
            url=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database="neo4j",
            index_name="Transcript",  # The same index name used when creating the vector store
            text_node_property="page_content",
            retrieval_query = """
            WITH node AS chunk, score AS similarity
                OPTIONAL MATCH (chunk)-[:MENTIONS]->(tool:Tool)
                OPTIONAL MATCH (chunk)-[:MENTIONS]->(challenge:Challenge)
                OPTIONAL MATCH (chunk)-[:MENTIONS]->(objective:Objective)
    
            WITH chunk, similarity, 
                collect(DISTINCT COALESCE(tool.id, "")) AS tools,  // Handle nulls
                collect(DISTINCT COALESCE(challenge.id, "")) AS challenges,  // Handle nulls
                collect(DISTINCT COALESCE(objective.id, "")) AS objectives  // Handle nulls
    
            RETURN '## Chunk Text: ' + chunk.page_content + '\n\n'
                + '### Tools: ' + reduce(str='', t IN tools | str + t + ', ') + '\n'
                + '### Challenges: ' + reduce(str='', ch IN challenges | str + ch + ', ') + '\n'
                + '### Objectives: ' + reduce(str='', o IN objectives | str + o + ', ') 
                AS text, 
                similarity AS score, 
                {source: chunk.id} AS metadata
            ORDER BY similarity ASC  // Best matches appear last
            """
        )

        results = neo4j_db.similarity_search(query, k=k)

        prompt = """
        You are an AI assistant helping to answer questions based on provided information. 
        The information you will use is authoritative, and you should only rely on it to construct your response. 
        You should never attempt to correct or verify the information using external sources or internal knowledge. 
        If the provided information is incomplete or insufficient to answer the question, respond with "I don't know" rather than making assumptions.

        Your goal is to construct a human-readable answer that is well-structured, clear, and relevant to the question.
        Please ensure that the answer uses all relevant parts of the provided information, formatted as necessary.
        Do not mention that your answer is based on the provided information.
        If you are provided with related entities (e.g., tools, challenges, objectives) connected to the information, include them in the answer appropriately.        
        Question: $query

        Context:
        $results
        """
        new_prompt = Template(prompt).substitute(query = query, results = results)
        response = client.chat.completions.create(messages=[{"role": "user","content": new_prompt,  }],model="gpt-4o-mini",)
        
        answer = response.choices[0].message.content.strip()

        return answer
        
    except RuntimeError as e:
        logger.error(f"Runtime error in perform_search(): {traceback.format_exc()}")
        raise

    except Exception as e:
        logger.critical(f"Unexpected error in perform_search(): {traceback.format_exc()}")
        raise RuntimeError("Unexpected error while performing search") from e

     