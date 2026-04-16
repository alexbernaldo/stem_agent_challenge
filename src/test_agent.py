import json
import pandas as pd

def testing(agent_state, dataset_path):
    
    dataset = pd.read_csv(dataset_path)

    python_code = agent_state["python_code"]
    
    namespace = {}
    
    
    try:
        exec(python_code, namespace)
        test_cleaned_data = namespace["clean_dataframe"](dataset)
        
        print("Dirty Dataset:\n")
        print("Null Values:")
        print(dataset.isnull().sum())
        print("\n Outliers in dataset:")
        print(dataset.shape)
        print("Cleaned Dataset:\n")
        print("Null Values:")
        print(test_cleaned_data.isnull().sum())
        print("\n Outliers in cleaned dataset:")
        print(test_cleaned_data.shape)
        
        return True, "Test passed successfully."
    except Exception as e:
        return False, f"Test failed with error: {str(e)}"