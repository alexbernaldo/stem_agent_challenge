import json
import pandas as pd

def testing(agent_state, dataset_path, eda_report):
    
    dataset = pd.read_csv(dataset_path)

    python_code = agent_state["python_code"]
    
    namespace = {}
    
    
    try:
        exec(python_code, namespace)
        test_cleaned_data = namespace["clean_dataframe"](dataset, eda_report)
        
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
        
        if test_cleaned_data.shape[0] == 0:
            return False, "The cleaned dataset is empty."
        else:
            if test_cleaned_data.shape[0]/dataset.shape[0] < 0.8:
                return False, "The cleaned dataset retains less than 80% of the original data, which may indicate excessive cleaning."
            else:
                return True, "Test passed successfully."

    except Exception as e:
        return False, f"Test failed with error: {str(e)}"