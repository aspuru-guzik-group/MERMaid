"""
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID
Runs on GPU

FILE 0
"""


from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
from safetensors.torch import load_file

import os
import json
import time
import requests
import io


def pdf_to_image(pdf_path):
	images = convert_from_path(pdf_path)
	return images

def tf_id_detection(image, model, processor):
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

# TO-DO: modify save directory
def save_image_from_bbox(image, annotation, page, output_dir):
	# the name should be page + label + index
	for counter, bbox in enumerate(annotation['bboxes']):
		#bbox = annotation['bboxes']
		label = annotation['labels'][counter]
		x1, y1, x2, y2 = bbox
		cropped_image = image.crop((x1, y1, x2, y2))
		cropped_image.save(os.path.join(output_dir, f"page_{page}_{label}_{counter}.png"))

def pdf_to_table_figures(pdf_path, model_id, safetensors_path, output_dir):

	model_id = "yifeihu/TF-ID-large"
	safetensors_path = "https://huggingface.co/yifeihu/TF-ID-base/resolve/main/model.safetensors"
 
	# response = requests.get(safetensors_path)
	# response.raise_for_status()
	# safetensors_file = io.BytesIO(response.content)
 
	pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
	output_dir = os.path.join(output_dir, pdf_name)

	os.makedirs(output_dir, exist_ok=True)

	images = pdf_to_image(pdf_path)
	print(f"PDF loaded. Number of pages: {len(images)}")
	# NOTE that this assumes we use a hugging face model and are not required to load the state_dict
	# commented out code is what we would need if we needed to load the state_dict ourselves
	# state_dict = load_file(safetensors_path)
	# state_dict = {}
	# with safe_open(safetensors_file, framework="torch") as f:
	# 	for key in f.keys():
	# 		state_dict[key] = f.get_tensor(key)
 	# model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
	model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
	processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
	print("Model loaded with retrained weights from: ", safetensors_path)
	
	print("=====================================")
	print("start saving cropped images")
	for i, image in enumerate(images):
		annotation = tf_id_detection(image, model, processor)
		save_image_from_bbox(image, annotation, i, output_dir)
		print(f"Page {i} saved. Number of objects: {len(annotation['bboxes'])}")
	
	print("=====================================")
	print("All images saved to: ", output_dir)

# model_id = "yifeihu/TF-ID-large"
# safetensors_path = "https://huggingface.co/yifeihu/TF-ID-base" # "./model_checkpoints/epoch_12/model.safetensors" #currently stored locally on cluster, will upload to huggingface or something?
# input_dir = "./pdfs/"
# output_dir = "./output/"

# for file in os.listdir(input_dir): 
# 	if not file.endswith("pdf"):
# 		continue 
# 	pdf_path = os.path.join(input_dir,file)
# 	pdf_to_table_figures(pdf_path, model_id, safetensors_path, output_dir)
