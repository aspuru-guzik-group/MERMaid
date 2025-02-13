import os
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
from safetensors.torch import load_file
import pdb
import torch

"""
Extracts all tables and figures from PDF documents, with the associated captions/
headings/footnotes, as images. 
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID
Runs on GPU 
"""


# from unittest.mock import patch
# from transformers.dynamic_module_utils import get_imports

# def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
#     if not str(filename).endswith("modeling_florence2.py"):
#         return get_imports(filename)
#     imports = get_imports(filename)
#     imports.remove("flash_attn")
#     return imports


#TODO: TO BE REPLACED
LARGE_MODEL_ID = "yifeihu/TF-ID-large" 
BASE_MODEL_ID = "yifeihu/TF-ID-base" 
LARGE_SAFETENSORS_PATH = "https://huggingface.co/yifeihu/TF-ID-base/resolve/main/model.safetensors" 
BASE_SAFETENSORS_PATH = "https://huggingface.co/yifeihu/TF-ID-base/resolve/main/model.safetensors" 


def _pdf_to_image(pdf_path):
	images = convert_from_path(pdf_path)
	return images


def _tf_id_detection(image, model, processor):
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


def _save_image_from_bbox(image, annotation, image_counter, output_dir, pdf_name):
	
    for counter, bbox in enumerate(annotation['bboxes']):
        x1, y1, x2, y2 = bbox
        cropped_image = image.crop((x1, y1, x2, y2))
        cropped_image.save(os.path.join(output_dir, f"{pdf_name}_image_{image_counter + counter + 1}.png"))
    return len(annotation["bboxes"]) + image_counter


def _create_model(model_id, safetensors_path, base_or_large):
    package_dir = os.path.dirname(__file__)
    safetensors_filename = base_or_large + "_model.safetensors"
    safetensors_download_path = package_dir + "/../safetensors/" + safetensors_filename
    # pdb.set_trace()
    if not os.path.exists(safetensors_download_path):
        torch.hub.download_url_to_file(safetensors_path, safetensors_download_path)

    state_dict = load_file(safetensors_download_path)
    model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    print("Model loaded with retrained weights from: ", safetensors_path)
    return model, processor


def _pdf_to_figures_and_tables(pdf_path, output_dir, large_model):
    # pdb.set_trace()
    os.makedirs(output_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images = _pdf_to_image(pdf_path)
    print(f"PDF {pdf_name} is loaded. Number of pages: {len(images)}")  
    
    if large_model:
        model, processor = _create_model(LARGE_MODEL_ID, LARGE_SAFETENSORS_PATH, "large")
    else:
        model, processor = _create_model(BASE_MODEL_ID, BASE_SAFETENSORS_PATH, "base")    
    
    print("=====================================")
    print("start saving cropped images")
    image_counter = 0
    for i, image in enumerate(images):
        annotation = _tf_id_detection(image, model, processor)
        image_counter = _save_image_from_bbox(image, annotation, image_counter, output_dir, pdf_name)
        print(f"Page {i} saved. Number of objects: {len(annotation['bboxes'])}")
    print("=====================================")
    print("All images saved to: ", output_dir)


def batch_pdf_to_figures_and_tables(input_dir: str, output_dir: str=None, large_model: bool=False):
    if not output_dir:
          output_dir = os.path.join(input_dir, "extracted_images")
    
    for file in os.listdir(input_dir): 
        if not file.endswith("pdf"):
            print("ERROR: " + file + "is not a pdf")
            continue
        pdf_path = os.path.join(input_dir,file)
        try:
            _pdf_to_figures_and_tables(pdf_path, output_dir, large_model)
        except Exception as e:
            print(e)
            print(f"pdf {pdf_path} cannot be processed.") 
            continue 