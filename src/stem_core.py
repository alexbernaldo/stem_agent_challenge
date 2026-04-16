from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import sandbox
import pandas as pd
import test_agent as test
import sandbox_eda
 
MAX_MUTATIONS = 20
MODEL_NAME = "gpt-4o"
META_PROMPT_EDA = open(os.path.join(os.path.dirname(__file__), "metaprompt_eda.txt"), "r").read()
META_PROMPT_CLEANING = open(os.path.join(os.path.dirname(__file__), "metaprompt_cleaning.txt"), "r").read()
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
    
    user_prompt_eda = "Generate a generic EDA script that analyzes any DataFrame and returns an eda_report dict following the interface contract."
    
    messages_eda = [
    {"role": "system", "content": META_PROMPT_EDA},
    {"role": "user", "content": user_prompt_eda}
    ]
    
    for i in range(MAX_MUTATIONS):
        agent_state = request_mutation(messages_eda)
        eda_success, eda_message = sandbox_eda.run_eda(agent_state["eda_code"], dataset_path)
        
        if eda_success == True:
            
            eda_report = eda_message
            break
        else:
            messages_eda.append({"role": "assistant", "content": json.dumps(agent_state)})
            messages_eda.append({"role": "user", "content": f"El código anterior no funcionó. El error fue: {eda_message}. Por favor, corrige el código y vuelve a intentarlo."})
            print(f"EDA Error iteración {i}: {eda_message}")
            
    else :
        raise RuntimeError("MAX MUTATIONS REACHED")
    
        ########################################################## SPECIALIZATION LOOP #######################################################
    
    print(f"EDA report: {eda_report}")
    
    user_prompt = f"Analiza el dataset e inicia la especialización.: {json.dumps(eda_report, indent=2)}"
    
    messages = [
    {"role": "system", "content": META_PROMPT_CLEANING},
    {"role": "user", "content": user_prompt}
    ]
    
    for i in range(MAX_MUTATIONS):
        agent_state = request_mutation(messages)
        success, message = sandbox.run_safeguard(agent_state["python_code"], dataset_path, eda_report)
        
        if success == True:
            test_success, test_message = test.testing(agent_state, dataset_path, eda_report)
            
            if test_success == True:
                freeze_agent(agent_state, f"agent_state_{i+1}.json")
                break
            else:
                messages.append({"role": "assistant", "content": json.dumps(agent_state)})
                messages.append({"role": "user", "content": f"El código anterior no funcionó. El error fue: {test_message}. Por favor, corrige el código y vuelve a intentarlo."})
        else:
            messages.append({"role": "assistant", "content": json.dumps(agent_state)})
            messages.append({"role": "user", "content": f"El código anterior no funcionó. El error fue: {message}. Por favor, corrige el código y vuelve a intentarlo."})
    else :
        raise RuntimeError("MAX MUTATIONS REACHED")
    
    


if __name__ == "__main__":
    run_stem_loop(os.path.join('data', 'monster_com-job_sample.csv'))