import os
import requests
import shutil
import base64
from .processor_info import DataRaiderInfo

"""
Filter images using OpenAI model
"""

def filter_images(info:DataRaiderInfo, 
                 prompt_directory:str, 
                 filter_prompt:str, 
                 image_directory:str): 
    """
    Determines if an image and its caption is relevant to the specified task.
    
    :param info: Global information required for processing containing API credentials and model details (must have `api_key` and `vlm_model` attributes).
    :type info: DataRaiderInfo
    :param prompt_directory: Path to the directory containing prompt files.
    :type prompt_directory: str
    :param filter_prompt: (Unused in the function; kept for future modifications).
    :type filter_prompt: str
    :param image_directory: Path to the directory containing images to be filtered.
    :type image_directory: str

    :return: None
    :rtype: None    
    """
    #create folders to separate relevant and irrelevant folders 
    relevant_folder = os.path.join(image_directory, "relevant_images")
    irrelevant_folder = os.path.join(image_directory, "irrelevant_images")
    if not os.path.exists(relevant_folder):
        os.makedirs(relevant_folder, exist_ok=True)
    if not os.path.exists(irrelevant_folder):
        os.makedirs(irrelevant_folder, exist_ok=True)

    #filter images 
    for file in os.listdir(image_directory):
        if (file.endswith(".png")):
            image_path = os.path.join(image_directory, file)
            print(f"Processing {image_path}")
            try: 
                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            except:
                print(f"Error reading image {image_path}")
                continue
        
            # Get filter prompt file
            user_prompt_path = os.path.join(prompt_directory, f"{filter_prompt}" + ".txt")
            with open(user_prompt_path, "r") as f:
                user_message = f.read().strip()
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
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
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
                response_data = response.json()['choices'][0]['message']['content']
                print(response_data)

                try: 
                    destination = "relevant_images" if "true" in response_data.lower() else "irrelevant_images"
                    destination_path = os.path.join(image_directory, f"{destination}/{file}")
                    if not os.path.exists(destination_path):
                        shutil.move(image_path, destination_path)
                        print(f"Moved {file} to {destination} folder")
                except Exception as e:
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Error during API request: {e}")