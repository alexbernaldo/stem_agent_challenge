from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import src.sandbox as sandbox
 
MAX_MUTATIONS = 5
MODEL_NAME = "gpt-4o"
META_PROMPT = open(os.path.join(os.path.dirname(__file__), "metaprompt.txt"), "r").read()

def request_mutation(messages):
    load_dotenv() 
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def freeze_agent(agent_state):
    

def run_stem_loop(dataset_path):