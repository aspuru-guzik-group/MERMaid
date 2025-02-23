import json
import os
import argparse
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables

def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    with open(config_file, 'r') as f:
        return json.load(f)

def main():
    """
    This function orchestrates loading the configuration, reading the input PDF directory, and
    calling the batch PDF processing function to extract images from PDFs.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Extract tables and figures from PDFs using VisualHeist.")
    parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
    parser.add_argument("--input_dir", type=str, help="Path to the input PDF directory", default=None)
    parser.add_argument("--output_dir", type=str, help="Path to the output image directory", default=None)
    parser.add_argument("--model_size", type=str, choices=["base", "large"], help="Model size to use", default=None)

    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)

    else:
        package_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(package_dir, 'startup.json')
        config = load_config(config_path) if os.path.exists(config_path) else {}

    input_dir = args.input_dir or config.get('pdf_dir', "./pdfs")
    output_dir = args.output_dir or config.get('image_dir', config.get('default_image_dir'))
    model_size = args.model_size or config.get('model_size', "base")
    use_large_model = model_size == "large"

    print(f"Processing PDFs in: {input_dir}")
    print(f"Saving extracted images to: {output_dir}")
    print(f"Using {'LARGE' if use_large_model else 'BASE'} model.")

    batch_pdf_to_figures_and_tables(input_dir, output_dir, large_model=model_size)

if __name__ == "__main__":
    main()