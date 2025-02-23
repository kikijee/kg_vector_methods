import requests
import glob
import json
import os
from string import Template
from timeit import default_timer as timer
from pydantic import BaseModel, Field
from typing import Optional, List
from ..utils.neo4j_util import save_to_neo4j

"""
[DOCUMENT]
-MENTIONS->
[objective] {"text": string}
[challange] {"text": string}
"""

class Entity(BaseModel):
    label: str 
    id: str 
    summary: Optional[str] 
    text: Optional[str] 

class GraphResponse(BaseModel):
    entities: List[Entity] 
    relationships: List[str]

OLLAMA_API_URL = "http://localhost:11434/api/chat"  # Change if using a different port

def generate_graph():
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
    label: 'Tool', id:string; //Tools that are talked about; `id` property is the specific tool mentioned in either the challenge or objective. This id should be in lowercase
    Note: There can possibly multiple challanges and objectives mentioned in one document, however keep these entities down to 2 each max.
    
    2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    Document|MENTIONS|Objective 
    Document|MENTIONS|Challenge
    Objective|HAS|Tool
    Challange|HAS|Tool

    3. The output should look like:
    {
        "entities": [{"label": "Objective","id":string,"text":string}],
        "relationships": ["documentid|HAS|objectiveid"]
    }

    Case Sheet:
    $ctext
    """

    results = []

    file_paths = glob.glob(r"./app/data/Copy_of_3548f8f6-f15f-493b-8338-01d0945629e6.txt")

    for file_path in file_paths:
        file_name = os.path.basename(file_path)

        with open(file_path, "r") as file:
            text = file.read().rstrip()  # Read and remove any trailing spaces

        prompt = Template(prompt_template).substitute(ctext=f"{file_name}\n\n{text}")

        payload = {
            "model": "deepseek-r1:14b",
            "messages": [{ "role": "user", "content": prompt }],
            "stream": False
        }

        try:
            response = requests.post(OLLAMA_API_URL, json=payload)
            
            response.raise_for_status()
            response_json = response.json()
            print(response_json)

            #generated_text = response_json.get("response", "").strip()

            results.append(json.loads(response_json))  # Convert response to JSON

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except json.JSONDecodeError:
            return {"error": "Failed to parse Ollama's response as JSON"}

    end = timer()
    print(f"Completed in {round(end - start, 2)} seconds\n")

    #save_to_neo4j(results)
    return results
