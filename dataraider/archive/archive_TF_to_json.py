from openai import OpenAI
import base64
import requests
import json
import os 
import cv2
import numpy as np
from os import listdir
import json
import glob

def reformat_json(input_file):
    with open(input_file, 'r') as file:
        json_content = file.read()
        json_content = json_content.replace("\"```json\\n", '').replace('```"', '').strip()       
        json_content = json_content.replace('\\n', '').replace('\\"', '"')
        data = json.loads(json_content)
        formatted_json = json.dumps(data, indent=4)

    # Write the formatted JSON to the output file
    with open(input_file, 'w') as file:
        file.write(formatted_json)

# OLD 
def image_crop(input_image, image_directory, output_directory):
  image_path = os.path.join(image_directory, f"{input_image}.png")
  image = cv2.imread(image_path)

  threshold = 254.5 # color threshold for a white pixel

  # specify the regions to split images
  region_start_1 = int(1/4*len(image))
  region_start_2 = int(5/8*len(image))
  region_end = len(image)

  percentage_threshold = 0.99 # percentage threshold for no. of white pixels
  step_size = 10 # step size for checking lines every n lines 

  # find the split lines 
  def find_split_line(image, threshold, region_start, 
                       region_end, percentage_threshold, 
                       step_size):
      gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
      _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
      white_pixel_count = np.count_nonzero(thresh == 255, axis=1)
      region_size = region_end - region_start
      split_line = region_start
      while split_line < region_end:
        min_white_pixels = int(percentage_threshold * len(thresh[split_line]))
        if white_pixel_count[split_line] >= min_white_pixels:
           break
        split_line += step_size
      return split_line
  
  split_line_1 = find_split_line(image, threshold, region_start_1, region_start_2, percentage_threshold, step_size)
  split_line_2 = find_split_line(image, threshold, region_start_2, region_end, percentage_threshold, step_size)

  def segment_image(image, split_line_1, split_line_2):
    top_segment = image[:split_line_1, :]
    middle_segment = image[split_line_1:split_line_2, :]
    bottom_segment = image[split_line_2:, :]
    return top_segment, middle_segment, bottom_segment
  
  top_segment, middle_segment, bottom_segment = segment_image(image, split_line_1, split_line_2)
  cv2.imwrite(os.path.join(output_directory, f"{input_image}_1.png"), top_segment)
  cv2.imwrite(os.path.join(output_directory, f"{input_image}_2.png"), middle_segment)
  cv2.imwrite(os.path.join(output_directory, f"{input_image}_3.png"), bottom_segment)

# OLD
def batch_image_crop(image_directory, output_directory):
  for image in os.listdir(image_directory): 
    if (image.endswith(".png")):
        image_name = image.removesuffix('.png')
        print (f"cropping {image_name}")
        try: 
          image_crop(image_name, image_directory, output_directory)
          print('Success')
        except Exception as e: 
          print(f'Failed: {e}')

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

#OLD  
def get_data(prompt_directory, image_name, image_directory, json_directory): 
    api_key = "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" 

    # Paths to images
    image_path1 = os.path.join(image_directory, f"{image_name}_1.png")
    image_path2 = os.path.join(image_directory, f"{image_name}_2.png")
    image_path3 = os.path.join(image_directory, f"{image_name}_3.png")
    #image_path4 = os.path.join(image_directory, f"{image_name}_4.png")
    response_path = os.path.join(json_directory, f"{image_name}_response_4o_w_cropping_promptv5-1.json")
    #token_path = os.path.join(f"{json_directory}/token_count/", f"{image_name}_tokencount_4o_w_cropping_promptv5-1.json")

    # Encode images to base64
    base64_image1 = encode_image(image_path1)
    base64_image2 = encode_image(image_path2)
    base64_image3 = encode_image(image_path3)
    #base64_image4 = encode_image(image_path4)

    # Read user message prompt
    user_prompt_path = os.path.join(prompt_directory, "rxn_opt_prompt_v5-1.txt")
    with open(user_prompt_path, "r") as file:
        user_message = file.read().strip()

    # Path for image caption (standard conditions)
    image_caption_path = os.path.join(image_directory, f"{image_name}.txt")

    # Construct messages with or without the image caption based on file existence
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
                        "url": f"data:image/jpeg;base64,{base64_image1}",
                    }
                }, 
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image2}",
                    }
                }, 
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image3}",
                    }
                }
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         "url": f"data:image/jpeg;base64,{base64_image4}",
                #     }
                # }                
            ]
        }
    ]

    # If the image caption file exists, append it to the messages content
    if os.path.exists(image_caption_path):
        with open(image_caption_path, "r") as file:
            image_caption = file.read().strip()
        messages[0]["content"].append({
            "type": "text",
            "text": image_caption
        })
        print('caption appended!')
    else: 
       print('no caption found!')

    # API request headers and payload
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": messages,
        "max_tokens": 4000
    }

    # Send API request
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise error if the request failed
        reaction_data = response.json()['choices'][0]['message']['content']
        token_count = response.json()['usage']

        # Save response
        with open(response_path, 'w') as json_file:
            json.dump(reaction_data, json_file)

        print(f"Reaction data saved to {response_path}!")

        #with open(token_path,'w') as token_file:
        #   json.dump(token_count, token_file)

        #print(f"Token count saved to {token_path}!")
        
        # Clean response
        try:
           reformat_json(response_path)
           print(f"{response_path}: Reaction data cleaned.")
        except Exception as e:
           print(f"{response_path}: Reaction data not cleaned.Error: {e}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")

# yet to test if appending works
def adaptive_get_data(prompt_directory, image_name, image_directory, json_directory):
    api_key = "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"
    
    # Find all subimages 
    image_paths = glob.glob(os.path.join(image_directory, f"{image_name}_*.png"))
    if not image_paths:
       print(f"No subimages found for {image_name}")
       return
    
    # Encode all images
    base64_images = []
    for image_path in image_paths:
       base64_images.append(encode_image(image_path))

    # Read user message prompt
    user_prompt_path = os.path.join(prompt_directory, "rxn_opt_prompt_v5-2.txt")
    with open(user_prompt_path, "r") as file:
       user_message = file.read().strip()

    # Path for image caption (if any)
    image_caption_path = os.path.join(image_directory, f"{image_name}.txt")

    # Path for response files 
    response_path = os.path.join(json_directory, f"{image_name}_response_4o_w_cropping_promptv5-2.json")
    token_path = os.path.join(f"{json_directory}/token_count/", f"{image_name}_tokencount_4o_w_cropping_promptv5-2.json")

    # Create base message 
    messages = [{
       "role": "user",
       "content": [
            {
                "type": "text",
                "text": user_message
            }
        ]
    }]

    # Add each encoded image as a separate entry
    for base64_image in base64_images:
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    # If the image caption file exists, append it to the messages content
    if os.path.exists(image_caption_path):
        with open(image_caption_path, "r") as file:
            image_caption = file.read().strip()
        messages[0]["content"].append({
            "type": "text",
            "text": image_caption
        })
        print('Caption appended!')
    else: 
        print('No caption found!')

    # API request headers and payload
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": messages,
        "max_tokens": 4000
    }

    # Send API request
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise error if the request failed
        reaction_data = response.json()['choices'][0]['message']['content']
        token_count = response.json()['usage']

        # Save responses
        with open(response_path, 'w') as json_file:
            json.dump(reaction_data, json_file)
        print(f"Reaction data saved to {response_path}!")

        with open(token_path, 'w') as token_file: 
           json.dump(token_count, token_file)
        print(f"Token count saved to {response_path}!")

        # Clean response
        try:
            reformat_json(response_path)
            print(f"{response_path}: Reaction data cleaned.")
        except Exception as e:
            print(f"{response_path}: Reaction data not cleaned. Error: {e}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")

def update_dict(prompt_directory, json_file, json_directory): 
    api_key = "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"  # Replace with your actual API key

    # Paths
    response_path = os.path.join(json_directory, f"{json_file}_updated_v2updateprompt.json")
    token_path = os.path.join(json_directory, f"{json_file}_updated_tokencount.json")

    # Read user message prompt
    user_prompt_path = os.path.join(prompt_directory, "rxn_opt_update_prompt_v3.txt")
    with open(user_prompt_path, "r") as file:
        user_message = file.read().strip()

    # Read json file
    json_path = os.path.join(json_directory, f"{json_file}.json")
    with open(json_path, "r") as file2:
        json_dict = file2.read().strip()

    # Construct messages with or without the image caption based on file existence
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
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": messages,
        "max_tokens": 4000
    }

    # Send API request
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise error if the request failed
        reaction_data = response.json()['choices'][0]['message']['content']
        token_count = response.json()['usage']

        # Save response
        with open(response_path, 'w') as json_file:
            json.dump(reaction_data, json_file)

        print(f"Reaction data saved to {response_path}!")

        # with open(token_path,'w') as token_file:
        #    json.dump(token_count, token_file)

        # print(f"Token count saved to {token_path}!")
        
        # Clean response
        try:
           reformat_json(response_path)
           print(f"{response_path}: Reaction data cleaned.")
        except Exception as e:
           print(f"{response_path}: Reaction data not cleaned.Error: {e}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")

# Batch processing
def batch_process(prompt_directory, cropped_image_directory, json_directory, ori_image_directory): 
    # Extract reaction dictionary
    for file in os.listdir(ori_image_directory):
        if (file.endswith(".png")):
            image_name = file.removesuffix('.png')
            print(f"processing {image_name}")
            adaptive_get_data(prompt_directory, image_name, cropped_image_directory, json_directory)
    print("#####################################")

    # Update reaction dictionary
    for file in os.listdir(json_directory):
        if (file.endswith(".json")):
            json_name = file.removesuffix('.json')
            print(f"updating {json_name}")
            update_dict(prompt_directory, json_name, json_directory)

prompt_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/"
cropped_image_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-cropped/"
json_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-cropped/output_v5/"
ori_image_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/prelim_test/"

# Single run
# response_path = os.path.join(json_directory, "RSC22_table_1_response_4o_w_cropping_promptv4_updated.json")
# reformat_json(response_path)

#image_name = "wiley23_table_1"
# json_name = "wiley31_actual_table_1_response_4o_w_cropping_promptv5-1"
#get_data(prompt_directory, image_name, cropped_image_directory, json_directory)
# update_dict(prompt_directory, json_name, json_directory)