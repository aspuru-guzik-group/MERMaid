import os
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
from safetensors.torch import load_file

"""
Extracts all tables and figures from PDF documents, with the associated captions/headings/footnotes, as images. 
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID
Runs on GPU 
"""

MODEL_ID = "yifeihu/TF-ID-large" #TODO: TO BE REPLACED
SAFETENSORS_PATH = "https://huggingface.co/yifeihu/TF-ID-base/resolve/main/model.safetensors" #TODO: TO BE REPLACED


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


def _save_image_from_bbox(image, annotation, output_dir, pdf_name):
	for counter, bbox in enumerate(annotation['bboxes']):
		x1, y1, x2, y2 = bbox
		cropped_image = image.crop((x1, y1, x2, y2))
		cropped_image.save(os.path.join(output_dir, f"{pdf_name}_image_{counter}.png"))


def _pdf_to_figures_and_tables(pdf_path, model_id, safetensors_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images = _pdf_to_image(pdf_path)
    print(f"PDF {pdf_name} is loaded. Number of pages: {len(images)}")
    state_dict = load_file(safetensors_path)
    model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    print("Model loaded with retrained weights from: ", safetensors_path)
    print("=====================================")
    print("start saving cropped images")
    for i, image in enumerate(images):
        annotation = _tf_id_detection(image, model, processor)
        _save_image_from_bbox(image, annotation, i, output_dir, pdf_name)
        print(f"Page {i} saved. Number of objects: {len(annotation['bboxes'])}")
    print("=====================================")
    print("All images saved to: ", output_dir)


def batch_pdf_to_figures_and_tables(input_dir: str, output_dir: str=None, model_id=MODEL_ID, safetensors_path=SAFETENSORS_PATH):
    if not output_dir:
          output_dir = os.path.join(input_dir, "extracted_images")
    
    for file in os.listdir(input_dir): 
        if not file.endswith("pdf"):
            print("ERROR: " + file + "is not a pdf")
            continue
        pdf_path = os.path.join(input_dir,file)
        try:
              _pdf_to_figures_and_tables(pdf_path, model_id, safetensors_path, output_dir)
        except Exception as e:
              print(f"pdf {pdf_path} cannot be processed.") 
              continue 