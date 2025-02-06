import cv2
import numpy as np
import os
import math

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

def find_last_line(image, threshold, region_start, region_end, percentage_threshold, step_size):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to identify white pixels
    _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)

    # Count the number of white pixels along the vertical axis
    white_pixel_count = np.count_nonzero(thresh == 255, axis=1)

    # Find the last line with at least the specified percentage of white pixels in the specified region
    split_line = region_end
    while split_line > region_start:
        min_white_pixels = int(percentage_threshold * len(thresh[split_line]))

        if white_pixel_count[split_line] >= min_white_pixels:
            break
        split_line -= step_size

    return split_line if split_line > region_start else region_start

def adaptive_split_lines(image, first_split_line, min_segment_height, threshold, percentage_threshold, step_size):
    # Calculate the remaining height after the first split line
    first_region_end = int(3/8 *len(image))
    remaining_height = image.shape[0] - first_region_end
    num_segments = math.ceil(remaining_height / min_segment_height)
    segment_height = remaining_height // num_segments  # Determine the approximate height of each segment

    split_lines = [first_split_line]  # Start with the first fixed split line
    region_start_list = [first_region_end] 

    for i in range(1, num_segments):
        # Calculate dynamic region start and end for each segment
        region_start = region_start_list[-1]
        region_end = region_start + segment_height
        region_start_list.append(region_end)

        # Find the split line for the current region
        split_line = find_last_line(image, threshold, region_start, region_end, percentage_threshold, step_size)
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

def process_image(image_name, image_directory, output_directory, min_segment_height=150):
    image_path = os.path.join(image_directory, f"{image_name}.png")
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Image {image_name}.png not found.")
        return
    
    # Set the threshold for white pixels
    threshold = 254.8

    # Set the percentage threshold for white pixels (e.g., 99.5%)
    percentage_threshold = 0.995

    # Set the step size for checking lines every n lines
    step_size = 10

    # Find the first split line within the first 1/4 of the image
    region_start_1 = int(1/4 * len(image))
    region_end_1 = int(3/8 *len(image))
    first_split_line = find_last_line(image, threshold, region_start_1, region_end_1, percentage_threshold, step_size)

    try: 
        # Find adaptive split lines based on the remaining height after the first split line
        split_lines = adaptive_split_lines(image, first_split_line, min_segment_height, threshold, percentage_threshold, step_size)

        # Check if split lines are valid
        if len(split_lines) < 1:
            raise ValueError(f"Error: Unable to find valid split lines for {image_name}. Saving original image.")

        # Crop the image into segments
        segments = crop_image(image, split_lines)

        # Check if cropped segments have valid size
        valid_segments = 0
        for idx, segment in enumerate(segments): 
            if segment.size > 0:
                cv2.imwrite(os.path.join(output_directory, f"{image_name}_{idx+1}.png"), segment)
                valid_segments += 1
            else: 
                print(f"Warning: Segment {idx+1} of {image_name} has zero size. Skipping.")
        
        if valid_segments == 0:
            raise ValueError(f"Error: No valid segments for {image_name}. Saving original image.")

    except Exception as e: 
        print(str(e))
        cv2.imwrite(os.path.join(output_directory, f"{image_name}_original.png"), image)

def batch_process_images(input_directory, output_directory, min_segment_height=120): 
    # Create a directory to save the cropped segments
    os.makedirs(output_directory, exist_ok=True)

    for file in os.listdir(input_directory):
        if (file.endswith('.png')):
            image_name = file.removesuffix('.png')
            print(f"processing {image_name}")
            process_image(image_name, input_directory, output_directory, min_segment_height)


# Batch process
input_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST/"
output_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-adaptivecrop/"
min_segment_height = 150

batch_process_images(input_directory, output_directory, min_segment_height)


