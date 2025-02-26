from openai import OpenAI
import glob
import json
import os
from string import Template
from ..config import settings
from timeit import default_timer as timer
import os
from pydantic import BaseModel
from typing import Optional, List
from langchain.prompts.prompt import PromptTemplate
from ..utils.neo4j_util import save_to_neo4j
from neo4j import GraphDatabase
from langchain_neo4j import GraphCypherQAChain
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from ..utils import data_retrieval_util
import logging
import traceback

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Entity(BaseModel):
    label: str 
    id: str 
    summary: Optional[str] 
    text: Optional[str] 

class GraphResponse(BaseModel):
    entities: List[Entity] 
    relationships: List[str]

def generate_graph ():
    try:
        client = OpenAI(api_key= settings.openai_api_key)
        start = timer()
        prompt_template = """
        From the Project Brief below, extract the following Entities & relationships described in the mentioned format 
        0. ALWAYS FINISH THE OUTPUT. Never send partial responses
        1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
        `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
        Entity Types:
        label:'Document',id:string,summary:string //Document is referencing the entire document; `summary` is a summary of the entire transcript; `id` is the file name included under Case Sheet before the transcript
        label:'Objective',id:string,text:string; //Objective that is mentioned in the text; `id` property is one word that summarizes the objective as a whole. This one word must only be in lowercase;`text` is the extracted body of text that talks about this objective, be sure that this field is the literal text from the document
        label:'Challenge',id:string,text:string; //Challenges that are talked about; `id` property is one word that summarizes the challange as a whole. This one word must only be in lowercase;`text` is the extracted body of text that talks about this challenge, be sure that this field is the literal text from the document
        label: 'Tool', id:string; //Please gather ALL the tools that are talked about; `id` property is the specific tool mentioned in either the challenge or objective. If there is a space please use an underscore instead. This id should be in lowercase; 
        Note: There can possibly be multiple challenges and objectives mentioned in one document limit 5 per `Challenge` and `Objective`
        
        2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
        Relationship types:
        Document|MENTIONS|Objective 
        Document|MENTIONS|Challenge
        Objective|HAS|Tool
        Challange|HAS|Tool


        3. The output should look like :
        {
            "entities": [{"label": "Objective","id":string,"text":string}],
            "relationships": ["documentid|HAS|objectiveid"]
        }

        Case Sheet:
        $ctext
        """
        
        results = []


        files = data_retrieval_util.fetch_files()

        for i in files: 

            file_name = i["metadata"]["file_name"]
            text = i["page_content"]
            
            prompt = Template(prompt_template).substitute(ctext = text)

            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",  # or "gpt-3.5-turbo"
                messages=[{"role": "system", "content": "You are an expert in graph representations."},
                        {"role": "user", "content": f"{file_name}\n{prompt}"}],
                temperature=0.5,
                response_format=GraphResponse
            )
            
            results.append(json.loads(response.choices[0].message.content)) #convert the response from gpt into a JSON 

        end = timer()
        print(f"Completed in {round(end - start, 2)} seconds\n")

        save_to_neo4j(results)
        return results
    
    except RuntimeError as e:
        logger.error(f"Runtime error in kg generate_graph(): {traceback.format_exc()}")
        raise

    except Exception as e:
        logger.critical(f"Unexpected error in kg generate_graph(): {traceback.format_exc()}")
        raise RuntimeError("Unexpected error while generating graph") from e


def query_graph(user_input):
    try:
        graph = Neo4jGraph(url = settings.neo4j_uri, username = settings.neo4j_user, password = settings.neo4j_password)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key = settings.openai_api_key,  
        )
        cypher_generation_template = """
        You are an expert Neo4j Cypher translator who converts English to Cypher based on the Neo4j Schema provided, following the instructions below:
        1. Generate Cypher query compatible ONLY for Neo4j Version 5
        2. Do not use EXISTS, SIZE, HAVING keywords in the cypher. Use alias when using the WITH keyword
        3. Use only Nodes and relationships mentioned in the given entity types below
        4. Always do a case-insensitive and fuzzy search for any properties related search. Eg: to search for a Tool, use `toLower(tool.id) contains 'neo4j'`.
        5. Never use relationships that are not mentioned in the given entity types below
        6. When asked about challenges or objectives, Match the properties using case-insensitive matching and the OR-operator, E.g, to find a logistics platform -project, use `toLower(objective.summary) contains 'logistics platform' OR toLower(objective.text) contains 'logistics platform' OR 'logistics platform' OR toLower(challenge.text) contains 'logistics platform' OR toLower(challenge.summary) contains 'logistics platform'`.

        Entity Types:
        label:'Document',id:string,summary:string //Document is referencing the entire document; `summary` is a summary of the entire transcript; `id` is the file name included under Case Sheet before the transcript
        label:'Objective',id:string,text:string; //Objective that is mentioned in the text; `id` property is one word that summarizes the objective as a whole. This one word must only be in lowercase;`text` is the extracted body of text that talks about this objective, be sure that this field is the literal text from the document
        label:'Challenge',id:string,text:string; //Challenges that are talked about; `id` property is one word that summarizes the challange as a whole. This one word must only be in lowercase;`text` is the extracted body of text that talks about this challenge, be sure that this field is the literal text from the document
        label: 'Tool', id:string; //Tools that are talked about; `id` property is the specific tool mentioned in either the challenge or objective. This id should be in lowercase

        Relationship types:
        Document|MENTIONS|Objective 
        Document|MENTIONS|Challenge
        Objective|HAS|Tool
        Challange|HAS|Tool

        Examples:
        Question: what is the common consensus on using selenium in throughout testing?
        Answer: ```
            MATCH (t:Tool {{id: "selenium"}})
            OPTIONAL MATCH (o:Objective)-[:HAS]->(t)
            OPTIONAL MATCH (c:Challenge)-[:HAS]->(t)
            OPTIONAL MATCH (o)<-[:MENTIONS]-(d:Document)
            OPTIONAL MATCH (c)<-[:MENTIONS]-(d:Document)
            RETURN t.id AS tool, 
                COLLECT(DISTINCT o.text) AS objectives, 
                COLLECT(DISTINCT c.text) AS challenges, 
                COLLECT(DISTINCT d.summary) AS documentSummaries
        ```

        Question: What tools developers use to support testing?
        Answer: ```
            MATCH (o:Objective)-[:HAS]->(t:Tool)
            OPTIONAL MATCH (o)<-[:MENTIONS]-(d:Document)
                RETURN t.id AS Tool, o.text AS ObjectiveText, d.summary as DocumentSummary
                ORDER BY t.id

        ```
        Question: How developers learn about the tools they use to support testing?
        Answer: ```
                    MATCH (o:Objective)-[:HAS]->(t:Tool)
                    RETURN o.id AS ObjectiveID, o.text AS ObjectiveDescription, t.id AS Tool, t.label AS ToolLabel
                    ORDER BY o.id
                ```

        Question: {question}
        """
        cypher_prompt = PromptTemplate(
            template = cypher_generation_template,
            input_variables = ["schema", "question"]
        )
        CYPHER_QA_TEMPLATE = """
            You are an assistant that helps to form nice and human understandable answers.
            The information part contains the provided information that you must use to construct an answer.
            The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
            Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
            If the provided information is empty, say that you don't know the answer.
            Final answer should be easily readable and structured.
            Information:
            {context}

            Question: {question}
            Helpful Answer:
            """
        qa_prompt = PromptTemplate(
                input_variables = ["context", "question"], template = CYPHER_QA_TEMPLATE
            )
    
        chain = GraphCypherQAChain.from_llm(
            llm = llm,
            graph = graph,
            verbose = True, 
            return_intermediate_steps = True, # detailed steps that led to the answer
            cypher_prompt = cypher_prompt, #helps guide ChatGPT in generating valid Cypher queries
            qa_prompt = qa_prompt, #defines the structure for answering questions
            allow_dangerous_requests = True
        )
        result = chain(user_input)
        return result
    except Exception as e:
        logger.error(f"Error in query_graph(): {traceback.format_exc()}")
        raise RuntimeError("Error query graph") from e

def answer_question(question):
    try:
        start = timer()
        result = query_graph(question)
        intermediate_steps = result["intermediate_steps"] #provides steps into the result
        cypher_query = intermediate_steps[0]["query"] #cypher query that was generated
        
        answer = result["result"]
        end = timer()
        print(f"Completed in {round(end - start, 2)} seconds\n")
        return answer, cypher_query
        
    except RuntimeError as e:
        logger.error(f"Runtime error in kg answer_question(): {traceback.format_exc()}")
        raise

    except Exception as e:
        logger.critical(f"Unexpected error in kg answer_question(): {traceback.format_exc()}")
        raise RuntimeError("Unexpected error generating answer") from e
    