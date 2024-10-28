from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError)
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
import os
import json
import time
from pathlib import Path

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


model_id = "yifeihu/TF-ID-large"
safetensors_path = "./model_checkpoints/epoch_12/model.safetensors"
image_dir = "./images/"
output_dir = "./output/temp/"

batch_img_to_caption_header(image_dir, model_id, safetensors_path, output_dir)