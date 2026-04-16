import subprocess
import tempfile
import json

def run_safeguard(code, dataset_path, eda_report):
    
    DATASET_PATH = f'DATASET_PATH = "{dataset_path}"\n'
    EDA_REPORT = f'eda_report = {json.dumps(eda_report)}\n'
    
    full_code = DATASET_PATH + EDA_REPORT + code
    
    try:
        code_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w").name
        
        with open(code_file, "w") as f:
            f.write(full_code)

        tmp_path = code_file
        
        result = subprocess.run(["python", tmp_path], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return (True, result.stdout)
        else:
            return (False, result.stderr)
        
    except subprocess.TimeoutExpired:
        return (False, "Execution timed out.")
    except Exception as e:
        return (False, str(e))