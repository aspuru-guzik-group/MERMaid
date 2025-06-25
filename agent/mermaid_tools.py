from pathlib import Path
import json
from langchain_core.tools import tool
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables, _pdf_to_figures_and_tables
from typing import Optional
import re
import subprocess
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

#CONSTANTS
PROMPT_DIR = Path(__file__).resolve().parent.parent / "Prompts"

with open(PROMPT_DIR / "inbuilt_keyvaluepairs.txt", 'r') as f:
    inbuilt_key_pair_file_contents = f.readlines()
AVAILABLE_KEYS =[]
for line in inbuilt_key_pair_file_contents:
    if not line.strip():
        continue
    key_pattern = r'"([^"]*)"'
    possible_keys = re.findall(key_pattern, line)
    if not possible_keys:
        continue
    AVAILABLE_KEYS.extend(possible_keys)


def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    config_file = Path(config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)

    script_dir = config_file.parent
    parent_dir = script_dir.parent
    for key in ['default_image_dir', 'default_json_dir', 'default_graph_dir']:
        val = config.get(key)
        if val and not Path(val).is_absolute():
            config[key] = str((parent_dir / val).resolve())
    return config
    

# @tool
# def visualheist_tool(pdf_dir:str="./", image_dir:str="./", model_size: str="base") -> str:
#     """Segments figures and tables from PDFs
#     """
#     batch_pdf_to_figures_and_tables(pdf_dir, image_dir, model_size=="large")
#     return "SUCCESS images saved succesfully to " + image_dir

@tool
def visualheist_tool(pdf_dir: str = "./", 
                     image_dir: Optional[str] = None, 
                     model_size: str = "base") -> str:
    """
    Segments figures and tables from PDFs.
    """
    pdf_path = Path(pdf_dir)
    if image_dir is None:
        if pdf_path.is_file():
            image_dir = str(pdf_path.parent)
            print(f'images will be saved to {image_dir}')
            _pdf_to_figures_and_tables(str(pdf_path), image_dir, model_size=="base")
        else:
            image_dir = str(pdf_path)
            print(f'images will be saved to {image_dir}')
            batch_pdf_to_figures_and_tables(str(pdf_path), image_dir, model_size=="base")
    return f"SUCCESS images saved successfully to {image_dir}"


@tool
def dataraider_tool(image_dir:str, 
                    json_dir:str, 
                    keys:list=None, 
                    new_keys:list=None) -> str:
    """
    Extracts information from tables and figures into JSON. 
    Parameters:
    - image_dir: Path to input folder of extracted figure/table images.
    - json_dir: Path to output folder for JSONs.
    - keys: List of pre-defined keys to extract.
    - new_keys: Optional new custom keys to extract.
    """
    
    if keys is None:
        keys = []
    if new_keys is None:
        new_keys = []
    image_dir = Path(image_dir)
    if json_dir is None: 
        json_dir = str(image_dir/"jsons")
    if not keys:
        print("WARNING: No keys provided, using default keys.")

    args = ["--image_dir", str(image_dir), "--prompt_dir", str(PROMPT_DIR), "--json_dir", str(json_dir)]
    if len(keys) != 0:
        args += ["--keys"] + keys
    if len(new_keys) != 0:
        args += ["--new_keys"] + new_keys
    
    subprocess.run(["dataraider"] + args)
    return "SUCCESS"
    

@tool
def kgwizard_tool(command:str="transform", json_dir:str="./", output_dir:str="", output_file:str="", schema:str="echem", sub_keys:list=[], sub_vals:list=[]) -> str:
    """Executes KGWizard with the parameters provided by the user via the Langchain agent
    Returns string which indicates whether files saved succesfully or not
    """
    if command == "transform":
        sub_dict = {}
        for i in range(0, len(sub_keys)):
            sub_dict[sub_keys[i]] = sub_vals[i]
        substitutions = [f"{k}:{v}" for k, v in sub_dict.items()]

        cli_args = [command, json_dir, "--output_file", output_file, "--output_dir", output_dir, "--schema", schema]
        if len(substitutions) > 0:
            cli_args += ["--substitutions"] + substitutions
    
    else: # command == "parse"
        cli_args = [command, output_dir, "--output_file", output_file, "--schema", schema]
    
    subprocess.run(["kgwizard"] + cli_args)
    return "SUCCESS"

#  If the key are not provided, 
#     ask the user to confirm which keys to extract. Available keys are: {', '.join(AVAILABLE_KEYS)}

if __name__ == "__main__":
    user_input = ""

    system_message = f""""
    You are a literature mining assistant. Use the tools provided to extract information from 
    literature papers. If dataraider_tool is used, check if the user provides keys to extract. 
    If yes, you must parse and pass the keys mentioned to the tool as a list e.g. ['Key1', 'Key2']. 
    Run the tool and return the results.
"""

    system_msg = SystemMessage(content=system_message)
    user_msg = HumanMessage(content=user_input)
    model = ChatOpenAI(model="gpt-4", temperature=0)
    agent = create_react_agent(model, tools=[visualheist_tool, dataraider_tool])
    response = agent.invoke({"messages": [system_msg, user_msg]})
    print(response)