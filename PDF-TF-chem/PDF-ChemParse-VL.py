"""
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID
Runs on GPU
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
import os
import json
import time

"""
For each PDF file in a directory, extract all tables and figures, with the 
associated captions/headings/footnotes as images. 

Args: 
pdf_path: str, path to the PDF file
model_id: str, model id of the TF-ID model
safetensors_path: str, path to the safetensors file
output_dir: str, path to the output directory

Output: 
each image is saved as a separate file in the output directory in the format 
{pdf_name}_image_{counter}.png 

"""
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

#TODO: check if the counter will overwrite the images 
def save_image_from_bbox(image, annotation, page, output_dir, pdf_name):
	for counter, bbox in enumerate(annotation['bboxes']):
		x1, y1, x2, y2 = bbox
		cropped_image = image.crop((x1, y1, x2, y2))
		cropped_image.save(os.path.join(output_dir, f"{pdf_name}_image_{counter}.png"))

def pdf_to_table_figures(pdf_path, model_id, safetensors_path, output_dir):
	pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
	os.makedirs(output_dir, exist_ok=True)

	images = pdf_to_image(pdf_path)
	print(f"PDF loaded. Number of pages: {len(images)}")
	state_dict = {}
	with safe_open(safetensors_path, framework="torch") as f:
		for key in f.keys():
			state_dict[key] = f.get_tensor(key)
	model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
	processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
	print("Model loaded with retrained weights from: ", safetensors_path)
	print("=====================================")
	print("start saving cropped images")
	for i, image in enumerate(images):
		annotation = tf_id_detection(image, model, processor)
		save_image_from_bbox(image, annotation, i, output_dir, pdf_name)
		print(f"Page {i} saved. Number of objects: {len(annotation['bboxes'])}")
	
	print("=====================================")
	print("All images saved to: ", output_dir)


if __name__ == "__main__":
	model_id = "yifeihu/TF-ID-large"
	safetensors_path = "./model_checkpoints/epoch_12/model.safetensors" #currently stored locally on cluster, will upload to huggingface
	input_dir = "./pdfs/"
	output_dir = "./output/"

	for file in os.listdir(input_dir): 
		if not file.endswith("pdf"):
			continue 
		pdf_path = os.path.join(input_dir,file)
		pdf_to_table_figures(pdf_path, model_id, safetensors_path, output_dir)
