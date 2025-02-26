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

class Entity(BaseModel):
    label: str 
    id: str 

class EntityResponse(BaseModel):
    entities: List[Entity]


def define_chunks():
    try:
        # Get all text files in the directory
        raw_files = glob.glob(r"./app/data/*.txt")
        
        # Chunking strategy: Each chunk will have at most 1000 characters
        # 20 characters will overlap between chunks to add context
        text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=20)

        # List to store chunked files separately
        chunked_files_list = []

        for file in raw_files:
            file_name = os.path.basename(file)  # Extract file name only, no directory

            with open(file, "r") as f:
                document = Document(page_content=f.read(), metadata={"file_name": file_name})
            
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
        return {"define_chunks error": str(e)}


    
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
        return {"kg_vector embed_data error": str(e)}
    
def create_index_for_vector(driver):
    try:
        # Create an index for the vector property on Chunk nodes
        with driver.session() as session:
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (c:Chunk) ON (c.vector)
            """)
        print("Index for 'vector' created successfully.")
    except Exception as e:
        print(f"Error creating index: {str(e)}")
    
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
    Note: There can possibly be multiple challenges and objectives mentioned in one chunk of text limit 2 per `Challenge` and `Objective`


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
        print("Error in extract_entities_from_text:", str(e))
        return {"entities":[]}


def insert_data(data):
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        #create_index_for_vector(driver)
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
        return {"kg_vector insert_data error": str(e)}

    

def generate_graph ():
    try:
        data = define_chunks()
        embed_data(data)
        transformed = insert_data(data)
        return{
            "message": "success",
            "data": transformed
        }
    except Exception as e:
        return {"kg_vector generate_graph error": str(e)}
    
     