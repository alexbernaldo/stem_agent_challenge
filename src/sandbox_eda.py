import subprocess
import tempfile
import json

def run_eda(code, dataset_path):
    
    
    DATASET_PATH = f'DATASET_PATH = "{dataset_path}"\n'
    
    full_code = DATASET_PATH + "import pandas as pd\ndataset = pd.read_csv(DATASET_PATH)\n" + code + "\nimport json\nprint(json.dumps(eda_report, default=str))\n"
    
    try:
        code_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w").name
        
        with open(code_file, "w") as f:
            f.write(full_code)

        tmp_path = code_file
        
        result = subprocess.run(["python", tmp_path], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            eda_report = json.loads(result.stdout)
            for col in eda_report.get('nulls', {}):
                eda_report['nulls'][col] = int(eda_report['nulls'][col])
            return (True, eda_report)
        else:
            return (False, result.stderr)
        
    except subprocess.TimeoutExpired:
        return (False, "Execution timed out.")
    except Exception as e:
        return (False, str(e))