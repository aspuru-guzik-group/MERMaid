import os
import requests
import glob
import json
from processor_info import DataRaiderInfo
from reaction_dictionary_formating import reformat_json

"""
Module for OpenAI APi access
"""

def update_dict_with_footnotes( 
                    info:DataRaiderInfo,
                    prompt_directory:str, 
                    update_dict_prompt:str, 
                    image_name:str, 
                    json_directory:str):
        """
        Updates the reaction dictionary with information from the footnote dictionary
        
        :param info: Global information required for processing
        :type info: DataRaiderInfo
        :param prompt_directory: Directory path to user message prompt
        :type prompt_directory: str
        :param update_dict_prompt: Directory path to update message prompt
        :type update_dict_prompt: str
        :param image_name: Name of image
        :type image_name: str
        :param json_directory: Path to directory of reaction dictionary
        :type update_dict_prompt: str
        
        :return: Returns nothing, all data saved in JSON
        :rtype: None
        """
        # Get user prompt file
        user_prompt_path = os.path.join(prompt_directory, f"{update_dict_prompt}.txt")
        with open(user_prompt_path, "r") as file:
            user_message = file.read().strip()
        
        # Get Json file
        json_path = os.path.join(json_directory, f"{image_name}.json")
        with open(json_path, "r") as file2:
            json_dict = file2.read().strip()

        # Replace existing json file with updated json file
        response_path = json_path

        # # Alternative: Save as a new json file
        # response_path = os.path.join(json_directory, f"{image_name}_updated.json")

        # Construct message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    },
                    {
                        "type": "text",
                        "text": json_dict
                    }              
                ]
            }
        ]

        # API request headers and payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {info.api_key}"
        }

        payload = {
            "model": info.vlm_model,
            "messages": messages,
            "max_tokens": 4000
        }

        # Send API request
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise error if the request failed
            reaction_data = response.json()['choices'][0]['message']['content']

            # Save response
            with open(response_path, 'w') as json_file:
                json.dump(reaction_data, json_file)
            print(f"Reaction dictionary has been updated with footnote description.")

            # Clean response
            try:
                info.reformat_json(response_path)
                print("Updated reaction dictionary has been cleaned.")
            except Exception as e:
                print("Updated reaction dictionary not cleaned.Error: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

def adaptive_get_data( 
                    info:DataRaiderInfo,
                    prompt_directory:str, 
                    get_data_prompt:str, 
                    image_name:str, 
                    image_directory:str, 
                    json_directory:str):
    """
    Retrieves a reaction dictionary from all subfigures and dumps into a JSON

    :param info: Global information required for processing
    :type info: DataRaiderInfo
    :param prompt_directory: Directory path to user message prompt
    :type prompt_directory: str
    :param get_data_prompt: File name of user message prompt to get reaction conditions
    :type get_data_prompt: str
    :param image_name: Name of image
    :type image_name: str
    :param image_directory: Root directory where the original images are stored
    :type image_directory: str
    :param json_directory: Output directory to save all output json files 
    :type json_directory: str

    :return: Returns nothing, all data saved in JSON
    :rtype: None
    """
    # Get all subfigures files 
    image_paths = glob.glob(os.path.join(image_directory, f"cropped_images/{image_name}_*.png"))
    if not image_paths:
        print(f"No subimages found for {image_name}")
        return

    base64_images = [info.encode_image(image_path) for image_path in image_paths]

    # Get user prompt file
    user_prompt_path = os.path.join(prompt_directory, f"{get_data_prompt}.txt")
    with open(user_prompt_path, "r") as file:
        user_message = file.read().strip()

    # Get response file paths
    if not os.path.exists(json_directory):
        os.makedirs(json_directory, exist_ok=True)

    image_caption_path = os.path.join(image_directory, f"{image_name}.txt")
    response_path = os.path.join(json_directory, f"{image_name}.json")

    # Create base message
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": user_message}]
    }]

    # Add each encoded image as a separate entry
    messages[0]["content"].extend({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
    } for base64_image in base64_images)
    
    # If the image caption file exists, append it to the messages content
    if os.path.exists(image_caption_path):
        with open(image_caption_path, "r") as file:
            image_caption = file.read().strip()
        messages[0]["content"].append({"type": "text","text": image_caption})

    # API request headers and payload
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {info.api_key}"
    }

    payload = {
        "model": info.vlm_model,
        "messages": messages,
        "max_tokens": 4000
    }

    # Send API request
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise error if the request failed
        reaction_data = response.json()['choices'][0]['message']['content']

        # Save responses
        with open(response_path, 'w') as json_file:
            json.dump(reaction_data, json_file)
        print(f"Reaction dictionary extracted.")

        # Clean response: 
        try: 
            reformat_json(response_path)
            print(f"{response_path}: Reaction data cleaned.")

        except Exception as e: 
            print(f"{response_path}: Reaction data not cleaned. Error: {e}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")