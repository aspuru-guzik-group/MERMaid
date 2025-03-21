from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel, Field
import json
from typing import List, Dict
from fastapi.responses import FileResponse
import subprocess
import os
import tempfile 
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("API key is missing in the environment variables.")
else: 
    print("API key is successfully retrieved!")

app = FastAPI()

STARTUP_JSON_PATH = Path(__file__).resolve().parent.parent / "scripts" / "startup.json"
USER_CONFIG_PATH = Path(__file__).resolve().parent.parent / "scripts" / "user_config.json"
PROMPT_DIR = Path(__file__).resolve().parent.parent / "Prompts"
VISUALHEIST_PATH = Path(__file__).resolve().parent.parent / "scripts" / "run_visualheist.py"
DATARAIDER_PATH = Path(__file__).resolve().parent.parent / "scripts" / "run_dataraider.py"
MERMAID_PATH = Path(__file__).resolve().parent.parent / "scripts" / "run_mermaid.py"
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class KGWizardConfig(BaseModel):
    address: str
    port: int
    graph_name: str
    schema: str
    dynamic_start: int
    dynamic_steps: int
    dynamic_max_workers: int


class Config(BaseModel):
    keys: List[str]
    new_keys: Dict
    pdf_dir: str
    image_dir: str
    json_dir: str
    graph_dir: str
    model_size: str
    kgwizard: KGWizardConfig
    prompt_dir: str = Field(default=str(PROMPT_DIR))
    
    class Config:
        from_attributes = True


@app.get("/inbuilt_keys")
def get_inbuilt_keys():
    inbuilt_keys = {}
    PROMPT_PATH = PROMPT_DIR / "inbuilt_keyvaluepairs.txt"
    with open(PROMPT_PATH, 'r', encoding="utf-8") as f:
        for line in f:
            if '":' in line:
                key, value = line.split('":', 1)
                key = key.strip().strip('"') 
                value = value.strip()
                inbuilt_keys[key] = value
    return inbuilt_keys


@app.post("/update_config/")
async def update_config(config: Config, file_name:str =str(USER_CONFIG_PATH)):
    config_dict = config.dict()

    # Read the startup.json file
    with open(STARTUP_JSON_PATH, 'r') as f:
        current_config = json.load(f)

    # Update the JSON with the new config values
    #TODO: check that my prompts link is still there and can be accessed
    current_config.update({
        "keys": config_dict["keys"],
        "new_keys": config_dict["new_keys"],
        "pdf_dir": config_dict["pdf_dir"],
        "image_dir": config_dict["image_dir"],
        "json_dir": config_dict["json_dir"],
        "graph_dir": config_dict["graph_dir"],
        "model_size": config_dict["model_size"],
        "prompt_dir": config_dict["prompt_dir"],
        "kgwizard": config_dict["kgwizard"]
        
    })

    # Save the updated config back to the JSON file
    with open(file_name, 'w') as f:
        json.dump(current_config, f, indent=4)

    return {"message": "User-defined configuration created successfully"}


@app.post("/upload/")
# async def upload_files(pdf: UploadFile = File(...), image: UploadFile = File(...)):
async def upload_files(pdf: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = UPLOAD_DIR / pdf.filename
        # image_path = Path(tmp_dir) / image.filename

        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(await pdf.read())

        # with open(image_path, "wb") as img_file:
        #     img_file.write(await image.read())

        # return {"pdf_path": str(pdf_path), "image_path": str(image_path)}
        return {"pdf_path": str(pdf_path)}


@app.get("/download_config")
def download_user_config():
    return FileResponse(USER_CONFIG_PATH, media_type="application/json", filename="user_config.json")


# Helper functions to get only the required arguments
def get_config_args():
    """Returns the config file argument."""
    return [
        "--config", USER_CONFIG_PATH
    ]

# Run full MERMaid pipeline
def run_mermaid_pipeline():
    """Runs the full MERMaid pipeline via subprocess."""
    result = subprocess.run(["python", "scripts/run_mermaid.py", "RUN"], capture_output=True, text=True)
    return result.stdout, result.stderr

# Run individual submodules
def run_visualheist():
    """Runs VisualHeist module."""
    result = subprocess.run(
        ["python", str(VISUALHEIST_PATH)] + get_config_args(),
        capture_output=True, text=True
    )
    print("RESULTS:", result)
    return result.stdout, result.stderr

def run_dataraider():
    """Runs DataRaider module."""
    result = subprocess.run(
        ["python", str(DATARAIDER_PATH)] + get_config_args(),
        capture_output=True, text=True
    )
    print("RESULTS:", result)
    return result.stdout, result.stderr

@app.get("/")
def home():
    return {"message": "Welcome to the MERMaid API"}

# Endpoint to run the full MERMaid pipeline
@app.post("/run_all")
def run_all_pipeline():
    stdout, stderr = run_mermaid_pipeline()
    response = {"output": stdout}
    if stderr:
        response["error"] = stderr
    return response

# Endpoint to run VisualHeist module
@app.post("/run_visualheist")
def visualheist():
    stdout, stderr = run_visualheist()
    response = {"output": stdout}
    if stderr:
        response["error"] = stderr
    return response

# Endpoint to run DataRaider module
@app.post("/run_dataraider")
def dataraider():
    stdout, stderr = run_dataraider()
    response = {"output": stdout}
    if stderr:
        response["error"] = stderr
    return response