from pathlib import Path
import json
from langchain_core.tools import tool
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent


PROMPT_DIR = Path(__file__).resolve().parent.parent / "Prompts"

import subprocess


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
    


@tool
def visualheist_tool(pdf_dir:str="./", image_dir:str="./", model_size: str="base") -> str:
    """Segments figures and tables from PDFs
    """
    batch_pdf_to_figures_and_tables(pdf_dir, image_dir, model_size=="large")
    return "SUCCESS images saved succesfully to " + image_dir


@tool
def dataraider_tool(image_dir:str="./", json_dir:str="./", keys:list=["Entry", "Catalyst", "Ligand", "Cathode", "Solvents", "Footnote"], new_keys:list=[]) -> str:
    """Extracts information from tables and figures into JSON
    """
    args = ["--image_dir", image_dir, "--prompt_dir", PROMPT_DIR, "--json_dir", json_dir]
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

model = init_chat_model("gpt-4", model_provider="openai")
from langchain_core.messages import HumanMessage

from langgraph.prebuilt import create_react_agent
# agent = create_react_agent(model, [dataraider_tool])
# mess = {"messages": [HumanMessage(content="Execute dataraider_tool on the image directory \
    # /home/wongbr55/MERMaid/dataraider_test json directory /home/wongbr55/MERMaid with the default keys and new keys")]}
agent = create_react_agent(model, [visualheist_tool, dataraider_tool])
mess = {"messages": [HumanMessage(content="Extract images from a pdf /home/wongbr55/MERMaid/visualheist_test")]}
response = agent.invoke(mess)
print(response)