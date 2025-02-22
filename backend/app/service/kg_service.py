from openai import OpenAI
import glob
import json
import os
from string import Template
from ..config import settings
from timeit import default_timer as timer
import os

"""
[DOCUMENT]
-MENTIONS->
[objective] {"text": string}
[challange] {"text": string}
"""

client = OpenAI(api_key= settings.openai_api_key)

def generate_graph ():
    start = timer()
    prompt_template = """
    From the Project Brief below, extract the following Entities & relationships described in the mentioned format 
    0. ALWAYS FINISH THE OUTPUT. Never send partial responses
    1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
    `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Document',id:string,summary:string //Document is referencing the entire document; `summary` is a summary of the entire transcript; `id` is the file name included under Case Sheet before the transcript
    label:'Objective',id:string,name:string;summary:string //Objective that is mentioned in the text; `id` property is one word that summarizes the objective as a whole. This one word must only be in lowercase.
    label:'Challenge',id:string,name:string; //Challenges that are talked about; `id` property is one word that summarizes the challenges as a whole.
    
    2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    Document|MENTIONS|Objective 
    project|MENTIONS|Challenge


    3. The output should look like :
    {
        "entities": [{"label": "Objective","id":string,"name":string,"summary":string}],
        "relationships": ["documentid|MENTIONS|objectiveid"]
    }

    Case Sheet:
    $ctext
     """
    
    results = []


    file = glob.glob(r"./app/data/Copy_of_3548f8f6-f15f-493b-8338-01d0945629e6.txt")


    file_path = file[0]
    
    file_name = os.path.basename(file_path)

    with open(file_path, "r") as file:
        text = file.read().rstrip()  # Read and remove any trailing spaces
    
    prompt = Template(prompt_template).substitute(ctext = text)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            messages=[{"role": "system", "content": "You are an expert in graph representations."},
                      {"role": "user", "content": f"{file_name}\n{prompt}"}],
            temperature=0.2,
        )
    except Exception as e:
        return {"error": str(e)}
    end = timer()
    print(f"Completed in {end - start} seconds\n")
    results.append(json.loads(response.choices[0].message.content)) #convert the response from gpt into a JSON 
    return results


