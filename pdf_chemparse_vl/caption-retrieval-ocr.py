from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError)
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
import os
import json
import time
from pathlib import Path

"""
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID
Runs on GPU

For each extracted image in a directory, extract the text portion (i.e. caption/header/
footnote) as images for subsequent OCR
#NOTE: OPTIONAL MODULE, might not be needed in the final pipeline.

Args: 
image_dir: str, path to the directory containing the images
model_id: str, model id of the TF-ID model
safetensors_path: str, path to the safetensors file
output_dir: str, path to the output directory

Output: 
each extracted caption image is saved as a separate file in the output directory in the format 
{image_name}_{label}_{counter}.png where {image_name} should be in the 
format {pdf_name}_image_{counter}. 

#TODO: might not need to save the caption images in the final pipeline, can pass 
result directly to OCR and store the text instead. 
#NOTE: Caption segmentation and OCR use different model and weights. 
"""

def caption_header_detect(image, model, processor):
	prompt = "<OD>"
	inputs = processor(text=prompt, images=image, return_tensors="pt")
	generated_ids = model.generate(
		input_ids=inputs["input_ids"],
		pixel_values=inputs["pixel_values"],
		max_new_tokens=1024,
		do_sample=False,
		num_beams=3
	)
	generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
	annotation = processor.post_process_generation(generated_text, task="<OD>", image_size=(image.width, image.height))
	return annotation["<OD>"]


def get_base_image_name(image_path): 
    return Path(image_path).stem


def caption_header_segment(image, image_path, annotation, output_dir):
	image_name = get_base_image_name(image_path)
      
	for counter, bbox in enumerate(annotation['bboxes']):
		label = annotation['labels'][counter]
		x1, y1, x2, y2 = bbox
		cropped_image = image.crop((x1, y1, x2, y2))
		cropped_image.save(os.path.join(output_dir, f"{image_name}_{label}_{counter}.png"))


def batch_img_to_caption_header(image_dir, model_id, safetensors_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    state_dict = {}
    with safe_open(safetensors_path, framework="torch") as f:
        for key in f.keys():
            state_dict[key] = f.get_tensor(key)
    model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    print("Model loaded with retrained weights from: ", safetensors_path)
    print("=====================================")
    print("start saving cropped captions/headers")
    
    for image_path in os.listdir(image_dir):
        image_path = os.path.join(image_dir, image_path)
        image_name = get_base_image_name(image_path)
        if image_path.endswith('.png'):
            image = Image.open(image_path)
            annotation = caption_header_detect(image, model, processor)
            caption_header_segment(image, image_path, annotation, output_dir)
            print(f"{image_name} is processed. Number of captions/headers identified: {len(annotation['bboxes'])}")
    print("-----------------------------------------")
    print("All captions and headers saved to:", output_dir)


#TODO: Clean output to not output as dictionary and not include <OCR> key:
def run_florence_ocr(task_prompt, image, model, processor, text_input=None):
    """run OCR on a single text image"""
    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input
    inputs = processor(text=prompt, 
                    images=image, 
                    return_tensors="pt")
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].cuda(),
        pixel_values=inputs["pixel_values"].cuda(),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3
        )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(image.width, image.height)
    )
    return parsed_answer

def process_images_ocr(pdf_names: list, image_dir: Path, caption_dir: Path, task_prompt: str):
    """batch process all text images in a directory""" 
    
    for base_file_name in pdf_names: 
        print(f"processing {base_file_name}")
        results = []
        
        for file in image_dir.iterdir():
            print(f'processing {file}')
            if file.name.startswith(base_file_name):
                image_path = file
                image = Image.open(image_path)
                response = run_florence_ocr(task_prompt, image)
                results.append(response)
        
        json_file_name = caption_dir / f"{base_file_name}.json"
        with open(json_file_name, 'w') as json_file: 
            json.dump(results, json_file, indent=4)
        print(f"Done processing {base_file_name}")   


if __name__ == "__main__":
    # Run caption segmentation model first 
    caption_model_id = "yifeihu/TF-ID-large"
    caption_safetensors_path = "./model_checkpoints/epoch_12/model.safetensors"
    image_dir = "./images/"
    caption_image_dir = "./output/temp/"
    batch_img_to_caption_header(image_dir, caption_model_id, caption_safetensors_path, caption_image_dir)

    # Run OCR on the extracted captions/headers
    pdf_dir = "./pdfs/"
    pdf_names = []
    for file in os.listdir(pdf_dir): #pdf_dir stores all original pdfs
         if file.endswith(".pdf"):
            pdf_name = file.removesuffix(".pdf")
            pdf_names.append(pdf_name)
    ocr_model_id = 'microsoft/Florence-2-large'
    ocr_model = AutoModelForCausalLM.from_pretrained(ocr_model_id, trust_remote_code=True).eval().cuda()
    ocr_processor = AutoProcessor.from_pretrained(ocr_model_id, trust_remote_code=True)
    caption_ocr_dir = "./output/temp/"
    task_prompt = '<OCR>'
    process_images_ocr(pdf_names, caption_image_dir, caption_ocr_dir, task_prompt)

