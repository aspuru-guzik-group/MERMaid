import json
import sys
import os
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables

def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    config['default_image_dir'] = os.path.join(parent_dir, config.get('default_image_dir', ''))
    config['default_json_dir'] = os.path.join(parent_dir, config.get('default_json_dir', ''))
    config['default_graph_dir'] = os.path.join(parent_dir, config.get('default_graph_dir', ''))
    return config

def main():
    """
    This function orchestrates loading the configuration, reading the input PDF directory, and
    calling the batch PDF processing function to extract images from PDFs.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Extract tables and figures from PDFs using VisualHeist.")
    parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
    parser.add_argument("--pdf_dir", type=str, help="Path to the input PDF directory", default=None)
    parser.add_argument("--image_dir", type=str, help="Path to the output image directory", default=None)
    parser.add_argument("--model_size", type=str, choices=["base", "large"], help="Model size to use", default=None)

    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)

    else:
        package_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(package_dir, 'startup.json')
        config = load_config(config_path) if os.path.exists(config_path) else {}

    pdf_dir = args.pdf_dir or config.get('pdf_dir', "./pdfs")
    image_dir = config.get('image_dir', "").strip() 
    if not image_dir: 
        image_dir = config.get('default_image_dir')
    # image_dir = args.image_dir or config.get('image_dir', config.get('default_image_dir'))
    model_size = args.model_size or config.get('model_size', "base")
    use_large_model = model_size == "large"

    print(f"Processing PDFs in: {pdf_dir}")
    print(f"Using {'LARGE' if use_large_model else 'BASE'} model.")

    batch_pdf_to_figures_and_tables(pdf_dir, image_dir, large_model=model_size)

if __name__ == "__main__":
    main()