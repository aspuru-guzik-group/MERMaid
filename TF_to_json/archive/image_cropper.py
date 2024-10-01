import cv2
import numpy as np
import os

# OLD 
def find_split_line(image, threshold, region_start, region_end, percentage_threshold, step_size):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to identify white pixels
    _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # Count the number of white pixels along the vertical axis
    white_pixel_count = np.count_nonzero(thresh == 255, axis=1)

    # Find the first line with at least the specified percentage of white pixels in the specified region
    split_line = region_start
    while split_line < region_end:
        min_white_pixels = int(percentage_threshold * len(thresh[split_line]))

        if white_pixel_count[split_line] >= min_white_pixels:
            break
        split_line += step_size

    return split_line if split_line < region_end else region_end

def adaptive_split_lines(image, min_segment_height, threshold, percentage_threshold, step_size):
    image_length = image.shape[0]
    num_segments = max(1, image_length // min_segment_height)  # Calculate number of segments based on minimum height
    segment_height = image_length // num_segments  # Determine the approximate height of each segment

    split_lines = []
    for i in range(1, num_segments):
        # Calculate dynamic region start and end for each segment
        region_start = segment_height * i
        region_end = segment_height * (i + 1) if i < num_segments - 1 else image_length

        # Find the split line for the current region
        split_line = find_split_line(image, threshold, region_start, region_end, percentage_threshold, step_size)
        split_lines.append(split_line)

    return split_lines

def crop_image(image, split_lines):
    # Crop the image into segments based on split lines
    segments = []
    prev_line = 0

    for split_line in split_lines:
        segments.append(image[prev_line:split_line, :])
        prev_line = split_line

    # Add the final segment (from the last split line to the end of the image)
    segments.append(image[prev_line:, :])

    return segments

def process_image(image_name, image_directory, output_directory, min_segment_height=200):
    image_path = os.path.join(image_directory, f"{image_name}.png")
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Image {image_name}.png not found.")
        return
    
    # Set the threshold for white pixels
    threshold = 254.5

    # Set the percentage threshold for white pixels (e.g., 99.5%)
    percentage_threshold = 0.995

    # Set the step size for checking lines every n lines
    step_size = 10

    

    try:
        # Find adaptive split lines based on the minimum segment height
        split_lines = adaptive_split_lines(image, min_segment_height, threshold, percentage_threshold, step_size)
        
        # Check if split lines are valid
        if len(split_lines) < 1:
            raise ValueError(f"Error: Unable to find valid split lines for {image_name}. Saving original image.")
        
        # Crop the image into segments
        segments = crop_image(image, split_lines)

        # Check if cropped segments have valid size
        if any(segment.size == 0 for segment in segments):
            raise ValueError(f"Error: Invalid cropped segments for {image_name}. Saving original image.")
        
        # Save the cropped segments
        for idx, segment in enumerate(segments):
            cv2.imwrite(os.path.join(output_directory, f"{image_name}_{idx+1}.png"), segment)
    except Exception as e: 
        print(str(e))
        cv2.imwrite(os.path.join(output_directory, f"{image_name}_original.png"), image)

def batch_process_image(input_directory, output_directory, min_segment_height=120): 
    # Create a directory to save the cropped segments
    os.makedirs(output_directory, exist_ok=True)

    for file in os.listdir(input_directory):
        if (file.endswith('.png')):
            image_name = file.removesuffix('.png')
            process_image(image_name, input_directory, output_directory, min_segment_height)
            print(f"{image_name} cropped and saved")
    print("Batch processing done!")

        
# # Batch process
# input_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST/"
# output_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-adaptivecrop/"
# min_segment_height = 120

# batch_process_image(input_directory,output_directory,min_segment_height)


from PIL import Image
image_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-adaptivecrop/"

for file in os.listdir(image_directory):
    if (file.endswith(".png")):
        image_name = file.removesuffix('.png')
        image_path = os.path.join(image_directory, file)
        with Image.open(image_path) as img: 
            width, height = img.size
        print(f"{image_name}: {height}")
