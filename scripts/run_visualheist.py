import json
import sys
import os
import argparse
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visualheist.methods_visualheist import batch_pdf_to_figures_and_tables
from pathlib import Path

def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    config_file = Path(config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    script_dir = config_file.parent
    parent_dir = script_dir.parent
    for key in ['default_image_dir', 'default_json_dir', 'default_graph_dir']:
        val = config.get(key)
        if val and not Path(val).is_absolute():
            config[key] = str((parent_dir / val).resolve())
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
        config = load_config(Path(args.config))

    else:
        package_dir = Path(__file__).resolve().parent.parent
        config_path = package_dir / "scripts" / "startup.json"
        config = load_config(config_path) if config_path.exists() else {}

    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else Path(config.get("pdf_dir", "./pdfs"))
    image_dir = config.get('image_dir', "").strip() 
    image_dir = Path(args.image_dir) if args.image_dir else Path(config.get("image_dir") or config.get("default_image_dir", "./images"))
    model_size = args.model_size or config.get('model_size', "base")
    print(f"Model size: {model_size}")
    use_large_model = model_size == "large"

    print(f"Processing PDFs in: {pdf_dir}")
    print(f"Saving images to: {image_dir}")
    print(f"Using {'LARGE' if use_large_model else 'BASE'} model.")

    batch_pdf_to_figures_and_tables(pdf_dir, image_dir, large_model=use_large_model)

if __name__ == "__main__":
    main()
