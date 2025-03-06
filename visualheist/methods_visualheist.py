import os
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM 
from safetensors import safe_open
from safetensors.torch import load_file
import torch
from huggingface_hub import hf_hub_download

"""
Extracts all tables and figures from PDF documents, with the associated captions/
headings/footnotes, as images. 
Adapted from TF-ID model https://github.com/ai8hyf/TF-ID 
"""


LARGE_MODEL_ID = "shixuanleong/visualheist-large" 
BASE_MODEL_ID = "shixuanleong/visualheist-base" 
LARGE_SAFETENSORS_PATH = "https://huggingface.co/shixuanleong/visualheist-large/resolve/main/model.safetensors" 
BASE_SAFETENSORS_PATH = "https://huggingface.co/shixuanleong/visualheist-base/resolve/main/model.safetensors" 


def _pdf_to_image(pdf_path):
    """Converts a pdf into a list of images
    :param pdf_path: Path to pdf
    :type pdf_path: str
    
    :return: List of Image instances
    :rtype: list[Image]
    """
    images = convert_from_path(pdf_path)
    return images


def _tf_id_detection(image, model, processor):
    
    """Performs table and figure identification using model and processor on image

    :param image: Image instance that refers to image we want to detect tables and figures from
    :type image: Image
    :param model: The pretrained causal language model used for text generation or inference.
    :type model: AutoModelForCausalLM
    :param processor: The processor that tokenizes input text for the model.
    :type processor: AutoProcessor

    :return: Dictionary of annotations done on image
    :rtype: dict
    """
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
    annotation = processor.post_process_generation(
        generated_text, task="<OD>", image_size=(image.width, image.height)
    )

    return annotation["<OD>"]


def _save_image_from_bbox(image, annotation, image_counter, output_dir, pdf_name):
    
    """Saves cropped regions denoted from annotation in image to output_dir

    :param image: Image instance that refers to image we would like to crop
    :type image: Image
    :param annotation: Dictionary that contains information on bounding boxes which correlate to points in image
    :type annotation: dict
    :param image_counter: Counter to how many images have been saved so far, used for file naming purposes
    :type image_counter: int
    :param output_dir: Directory to store the segmented images
    :type output_dir: str
    :param pdf_name: Name of the pdf in which image comes from, used for file naming purposes
    :type pdf_name: str

    :return: The new image_counter after saving all cropped images
    :rtype: int
    """
    
    for counter, bbox in enumerate(annotation['bboxes']):
        x1, y1, x2, y2 = bbox
        cropped_image = image.crop((x1, y1, x2, y2))
        cropped_image.save(os.path.join(output_dir, f"{pdf_name}_image_{image_counter + counter + 1}.png"))
    return len(annotation["bboxes"]) + image_counter


def _create_model(model_id, safetensors_path, base_or_large):
    
    """Intializes model used for segmenting tables and figures using either the base or large model

    :param model_id: Model id to use, either LARGE_MODEL_ID or BASE_MODEL_ID
    :type model_id: str
    :param safetensors_path: Path to safetensors for model, either LARGE_SAFETENSORS_PATH or BASE_SAFETENSORS_PATH
    :type safetensors_path: str
    :param base_or_large: String is either 'base' or 'large' depending on whether we use base or large model
    :type base_or_large: str
    

    :return: Returns the model and processor that allows for 
    :rtype: tuple[AutoModelForCausalLM, AutoProcessor]
    """
    
    package_dir = os.path.dirname(__file__)
    safetensors_filename = base_or_large + "_model.safetensors"
    safetensors_download_path = package_dir + "/../safetensors/" + safetensors_filename
    if not os.path.exists(safetensors_download_path):
        safetensors_download_path = hf_hub_download(repo_id=model_id, filename="model.safetensors")
        # torch.hub.download_url_to_file(safetensors_path, safetensors_download_path)

    state_dict = load_file(safetensors_download_path)
    model = AutoModelForCausalLM.from_pretrained(model_id, state_dict=state_dict, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    # print("Model loaded with retrained weights from: ", safetensors_path)
    return model, processor


def _pdf_to_figures_and_tables(pdf_path, output_dir, large_model):
    
    """Takes a singke pdf and runs either LARGE_MODEL_ID or BASE_MODEL_ID on it to extract tables and figures.
    Saves the results in output_dir
    
    :param pdf_path: Path to a single pdf
    :type input_dir: str
    :param output_dir: Directory to where segmented tables and figures are located
    :type output_dir: str
    :param large_model: Whether we use the large or base model when performing table-figure extraction
    :type large_model: bool
    
    :return: Returns nothing, all segmented figures and tables are saved seperatly
    :rtype: None
    """
    
    os.makedirs(output_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images = _pdf_to_image(pdf_path)
    print(f"PDF {pdf_name} is loaded.")  
    
    if large_model:
        model, processor = _create_model(LARGE_MODEL_ID, LARGE_SAFETENSORS_PATH, "large")
    else:
        model, processor = _create_model(BASE_MODEL_ID, BASE_SAFETENSORS_PATH, "base")    
    
    image_counter = 0
    for i, image in enumerate(images):
        annotation = _tf_id_detection(image, model, processor)
        image_counter = _save_image_from_bbox(image, annotation, image_counter, output_dir, pdf_name)
        print(f"Page {i} saved. Number of objects: {len(annotation['bboxes'])}")
    print(f"All extracted images from {pdf_name} are saved")
    print("=====================================")


def batch_pdf_to_figures_and_tables(input_dir, output_dir=None, large_model=False):
    """Takes a directory of pdfs via input_dir and saves tables and figures in output_dir
    
    :param input_dir: Input directory to pdfs
    :type input_dir: str
    :param output_dir: Directory to where segmented tables and figures are located, defaults to None
    :type output_dir: str
    :param large_model: Whether we use the large or base model when performing table-figure extraction, defaults to False
    :type large_model: bool
    
    :return: None, all files will be saved in output_dir
    :rtype: None
    """
    
    if not output_dir:
          output_dir = os.path.join(input_dir, "extracted_images")
    
    for file in os.listdir(input_dir): 
        if not file.endswith("pdf"):
            print("ERROR: " + file + " is not a pdf")
            continue
        pdf_path = os.path.join(input_dir,file)
        try:
            _pdf_to_figures_and_tables(pdf_path, output_dir, large_model)
        except Exception as e:
            print(e)
            print(f"pdf {pdf_path} cannot be processed.") 
            continue 