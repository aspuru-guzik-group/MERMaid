import streamlit as st
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os
#TODO: user need to create an .env file with OPENAI_API_KEY=<USER_API_KEY>

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

if api_key is None:
    st.error("API key is missing in the environment. Please add it to the .env file.")
else:
    st.success("API key is successfully retrieved!")

# Endpoint of the FastAPI backend
API_URL = "http://127.0.0.1:8000"

# Display form for user inputs
st.title("MERMaid Pipeline")

# Keys selection
response = requests.get(f"{API_URL}/inbuilt_keys")
if response.status_code == 200:
    inbuilt_keys = response.json()
else:
    inbuilt_keys = {}

keys = st.multiselect(
    "Select Keys",
    options=[key for key in inbuilt_keys.keys()],
    format_func=lambda x: f"{x} - {inbuilt_keys.get(x, '')}"
)

# Optional: add new keys
st.subheader("Add Custom Keys (Optional)")
if 'custom_keys' not in st.session_state:
    st.session_state.custom_keys = []

add_key_button = st.button("Add Custom Key")
if add_key_button:
    st.session_state.custom_keys.append({"key": "", "description": ""})

new_keys = {}
for idx, custom_key in enumerate(st.session_state.custom_keys):
    key_input = st.text_input(f"Enter Custom Key {idx+1}", custom_key['key'])
    description_input = st.text_input(f"Enter Description for Key {idx+1}", custom_key['description'])
    st.session_state.custom_keys[idx]['key'] = key_input
    st.session_state.custom_keys[idx]['description'] = description_input
    if key_input and description_input:
        new_keys[key_input] = description_input

#PDF upload 
uploaded_pdf = st.file_uploader("Upload PDF to analyze", type="pdf")
if uploaded_pdf:
    response = requests.post(f"{API_URL}/upload/", files={"pdf": uploaded_pdf})
    if response.status_code == 200:
        pdf_path = response.json().get("pdf_path")
        st.success(f"PDF saved temporarily to: {pdf_path}")
        pdf_dir = str(Path(pdf_path).parent)
    else:
        st.error("Error uploading PDF")
# Form fields for other configuration settings
image_dir = st.text_input("Local directory to save extracted images", "/path/to/images")
json_dir = st.text_input("Local directory to save reaction JSON dictionaries", "/path/to/json")
graph_dir = st.text_input("Local directory to save graph file", "/path/to/graphs")
model_size = st.selectbox("Select VisualHeist Model Size", ["BASE", "LARGE"])

kgwizard_address = st.text_input("KGWizard Address", "ws://localhost")
kgwizard_port = st.number_input("KGWizard Port", value=8182)
kgwizard_graph_name = st.text_input("Graph Name", "g")
kgwizard_schema = st.text_input("Schema Name", "echem")
kgwizard_dynamic_start = st.number_input("Dynamic Start", value=1)
kgwizard_dynamic_steps = st.number_input("Dynamic Steps", value=5)
kgwizard_dynamic_max_workers = st.number_input("Dynamic Max Workers", value=15)

# Select pipeline to run
st.subheader("Choose Pipeline to Run")
pipeline_option = st.radio(
    "Select Pipeline",
    ["Run Full Pipeline", "Run VisualHeist", "Run DataRaider"]
)

# Submit the form
if st.button("Save Configuration"):
    # Create a config dictionary
    config = {
        "keys": keys,
        "new_keys": new_keys,
        "pdf_dir": pdf_dir,
        "image_dir": image_dir,
        "json_dir": json_dir,
        "graph_dir": graph_dir,
        "model_size": model_size,
        "kgwizard": {
            "address": kgwizard_address,
            "port": kgwizard_port,
            "graph_name": kgwizard_graph_name,
            "schema": kgwizard_schema,
            "dynamic_start": kgwizard_dynamic_start,
            "dynamic_steps": kgwizard_dynamic_steps,
            "dynamic_max_workers": kgwizard_dynamic_max_workers,
        }
    }
    # Send data to FastAPI backend
    response = requests.post(f"{API_URL}/update_config/", json=config)
    
    if response.status_code == 200:
        st.success("Configuration updated successfully!")

        # allow user to download the updated configuration file
        download_url = f"{API_URL}/download_config" 
        download_response = requests.get(download_url)
        if download_response.status_code == 200:
            st.download_button(
                label="Download Configuration",
                data=download_response.content,
                file_name="user_config.json",
                mime="application/json"
            )
        else:
            st.error("Error downloading configuration.")
    else:
        st.error("Error updating configuration.")
    
# Trigger pipeline based on user selection
if st.button("Run Selected Pipeline"):
    if pipeline_option == "Run Full Pipeline":
        response = requests.post(f"{API_URL}/run_all")
    elif pipeline_option == "Run VisualHeist":
        response = requests.post(f"{API_URL}/run_visualheist")
    elif pipeline_option == "Run DataRaider":
        response = requests.post(f"{API_URL}/run_dataraider")

    # Display the output of the selected pipeline
    if response.status_code == 200:
        st.success(f"Pipeline executed successfully. Check your results!")
    else:
        st.error(f"Error executing pipeline: {response.json().get('error', 'Unknown error')}")

