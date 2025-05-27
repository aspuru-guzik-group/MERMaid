import os
import requests
import shutil
import base64
from .processor_info import DataRaiderInfo
from pathlib import Path
import json

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
    :param filter_prompt: Path to the filter prompt.
    :type filter_prompt: str
    :param image_directory: Path to the directory containing images to be filtered.
    :type image_directory: str

    :return: None
    :rtype: None    
    """
    prompt_directory = Path(prompt_directory)
    image_directory = Path(image_directory)

    #create folders to separate relevant and irrelevant folders 
    relevant_folder = image_directory / "relevant_images"
    irrelevant_folder = image_directory /"irrelevant_images"
    relevant_folder.mkdir(parents=True, exist_ok=True)
    irrelevant_folder.mkdir(parents=True, exist_ok=True)
    #filter images 
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}

    for file in image_directory.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            print(f"Processing {file}")
            try: 
                with open(file, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Error reading image {file}:{e}")
                continue
        
            # Get filter prompt file
            user_prompt_path = prompt_directory / f"{filter_prompt}.txt"
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

                try: 
                    destination = "relevant_images" if "true" in response_data.lower() else "irrelevant_images"
                    destination_path = image_directory / destination / file.name
                    if not destination_path.exists():
                        shutil.move(str(file), str(destination_path))
                        print(f"Moved {file} to {destination} folder")
                except Exception as e:
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Error during API request: {e}")

def check_segmentation(info:DataRaiderInfo, 
                 prompt_directory:str, 
                 image_directory:str,
                 check_prompt:str="check_image_prompt"
                 ): 
    """
    Determines if the image segmentation is done properly.
    
    :param info: Global information required for processing containing API credentials and model details (must have `api_key` and `vlm_model` attributes).
    :type info: DataRaiderInfo
    :param prompt_directory: Path to the directory containing prompt files.
    :type prompt_directory: str
    :param check_prompt: Path to the prompt.
    :type check_prompt: str
    :param image_directory: Path to the directory containing images to be filtered.
    :type image_directory: str

    :return: None
    :rtype: None    
    """
    #create folders to separate properly and improperly segmented images 
    prompt_directory = Path(prompt_directory)
    image_directory = Path(image_directory)
    image_directory = image_directory / "relevant_images/"
    #Check if the image directory exists
    if not image_directory.exists():    
        print(f"Image directory {image_directory} does not exist.")
        return
    # properly_segmented_folder = image_directory / "properly_segmented_images"
    improperly_segmented_folder = image_directory / "improperly_segmented_images"
    # log_folder = improperly_segmented_folder / "logs"
    # properly_segmented_folder.mkdir(parents=True, exist_ok=True)
    improperly_segmented_folder.mkdir(parents=True, exist_ok=True)
    # log_folder.mkdir(parents=True, exist_ok=True)
    
    #filter images 
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}

    for file in image_directory.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            # print(f"\nProcessing {file}")
            try: 
                with open(file, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Error reading image {file}:{e}")
                continue
        
            # Get filter prompt file
            user_prompt_path = prompt_directory / f"{check_prompt}.txt"
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

                try: 
                    is_proper = "true" in response_data.lower()
                    if not is_proper:
                        destination_path = improperly_segmented_folder / file.name
                        if not destination_path.exists():
                            shutil.move(str(file), str(destination_path))
                        # print(f"Moved {file} to {destination} folder")
                    
                        try: 
                            response_json = json.loads(response_data)
                        except json.JSONDecodeError:
                            response_json = {"raw_response": response_data}
                        log_file_path = improperly_segmented_folder / f"{file.stem}_segmentation_error_log.json"
                        with open(log_file_path, "w") as log_file:
                            json.dump(response_json, log_file, indent=2)
                            # print(f"Log saved for {file.name} at {log_file_path}\n")
                except Exception as e:
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Error during API request: {e}")