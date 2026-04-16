from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import sandbox
import pandas as pd
import test_agent as test
 
MAX_MUTATIONS = 10
MODEL_NAME = "gpt-4o"
META_PROMPT = open(os.path.join(os.path.dirname(__file__), "metaprompt.txt"), "r").read()
load_dotenv() 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

def request_mutation(messages):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def freeze_agent(agent_state, output_path):
    with open(output_path, "w") as f:
        json.dump(agent_state, f, indent=4)
    
    print("Exito")



def run_stem_loop(dataset_path):
    
    dataset = pd.read_csv(dataset_path)
    
    user_prompt = f"Analiza el dataset e inicia la especialización.: {dataset.to_string()}"
    
    messages = [
    {"role": "system", "content": META_PROMPT},
    {"role": "user", "content": user_prompt}
    ]
    
    for i in range(MAX_MUTATIONS):
        agent_state = request_mutation(messages)
        success, message = sandbox.run_safeguard(agent_state["python_code"], dataset_path)
        
        
        if success == True:
            test_success, test_message = test.testing(agent_state, dataset_path)
            
            if test_success == True:
                freeze_agent(agent_state, f"agent_state_{i+1}.json")
                break
            else:
                messages.append({"role": "assistant", "content": agent_state["python_code"]})
                messages.append({"role": "user", "content": f"El código anterior no funcionó. El error fue: {test_message}. Por favor, corrige el código y vuelve a intentarlo."})
        else:
            messages.append({"role": "assistant", "content": agent_state["python_code"]})
            messages.append({"role": "user", "content": f"El código anterior no funcionó. El error fue: {message}. Por favor, corrige el código y vuelve a intentarlo."})
    else :
        raise RuntimeError("MAX MUTATIONS REACHED")
    


if __name__ == "__main__":
    run_stem_loop(os.path.join('data', 'dirty_dataset.csv'))