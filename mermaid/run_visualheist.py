import json
from methods_visualheist import batch_pdf_to_figures_and_tables

def load_config(config_file):
    
    with open(config_file, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Load the configuration from the file
    config = load_config('./mermaid/startup.json')

    # Use the default configuration in the function call if unspecified 
    input_dir = config.get('pdf_dir', "./pdfs")
    output_dir = config.get('image_dir', config.get('default_image_dir'))

    # Use the loaded configuration in the function call
    batch_pdf_to_figures_and_tables(input_dir, output_dir, large_model=False)