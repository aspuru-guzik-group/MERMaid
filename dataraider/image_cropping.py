import os
import cv2
import numpy as np
import math

""" 
Module for cropping images based off of split lines
"""

def _find_split_line(image, 
                    threshold, 
                    region_start, 
                    region_end, 
                    percentage_threshold, 
                    step_size):
    """Helper function to determine where to segment figure

    :param image: OpenCV image
    :type image: numpy.ndarray
    :param threshold: Thershold for identifying white pixels
    :type threshold: float
    :param region_start: Starting row of finding split line
    :type region_start: int
    :param region_end: Ending row of finding split line
    :type region_end: int
    :param percentage_threshold: Minimum portion of white pixels required for row to be considered a line
    :type percentage_threshold: float
    :param step_size: Number of rows to skip per line check
    :type step_size: int
    
    :return: Returns the index of the split line
    :rtype: int
    """
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Convert the image to grayscale            
    _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY) # Identify white pixels
    white_pixel_count = np.count_nonzero(thresh == 255, axis=1) 

    # Find the last line with >= the specified percentage of white pixels in the specified region
    split_line = region_end
    while split_line > region_start:
        min_white_pixels = int(percentage_threshold * len(thresh[split_line]))

        if white_pixel_count[split_line] >= min_white_pixels:
            break
        split_line -= step_size

    return split_line if split_line > region_start else region_start

def _adaptive_split_lines(image, 
                            first_split_line, 
                            min_segment_height, 
                            threshold, 
                            percentage_threshold, 
                            step_size):
    """
    Helper function to identify all the split lines for an image
    
    :param image: OpenCV image
    :type image: numpy.ndarray
    :param first_split_line: Index of the first split line
    :type first_split_line: int
    :param min_segment_height: minimum height of each segmented subfigure, defaults to 120
    :type min_segment_height: int
    :param threshold: Thershold for identifying white pixels
    :type threshold: float
    :param percentage_threshold: Minimum portion of white pixels required for row to be considered a line
    :type percentage_threshold: float
    :param step_size: Number of rows to skip per line check
    :type step_size: int
    
    :return: Returns the list of indicies of split lines
    :rtype: list[int]
    """
    
    # Calculate the remaining height after the first split line
    first_region_end = int(3/8 *len(image))
    remaining_height = image.shape[0] - first_region_end
    num_segments = math.ceil(remaining_height / min_segment_height)
    segment_height = remaining_height // num_segments  # Determine the approximate height of each segment

    split_lines = [first_split_line]  # Start with the first fixed split line
    region_start_list = [first_region_end] 

    for __ in range(1, num_segments):
        # Calculate dynamic region start and end for each segment
        region_start = region_start_list[-1]
        region_end = region_start + segment_height
        region_start_list.append(region_end)

        # Find the split line for the current region
        split_line = _find_split_line(image, threshold, region_start, region_end, percentage_threshold, step_size)
        split_lines.append(split_line)

    return split_lines

def _segment_image(image, split_lines):
    """
    Helper function to crop image based on split lines
    
    :param image: OpenCV image
    :type image: numpy.ndarray
    :param split_lines: list of split lines
    :type split_lines: list[int]
    
    :return: Returns the different segments of image that were cropped with split_lines
    :rtype: list[numpy.ndarray]
    """
    segments = []
    prev_line = 0

    for split_line in split_lines:
        segments.append(image[prev_line:split_line, :])
        prev_line = split_line

    segments.append(image[prev_line:, :]) # Add the final segment (from the last split line to the end of the image)

    return segments


def crop_image(image_name:str, 
                image_directory:str, 
                min_segment_height=120): 
        """
        Adaptively crop a given figure into smaller subfigures before 
        passing to VLM based on image length and save to image_directory

        parameters: 
        :param image_name: Base image name
        :type image_name: str
        :param image_directory: Root directory where original images are saved
        :type image_directory: str
        :param min_segment_height: Minimum height of each segmented subfigure, defaults to 120
        :type min_segment_height: int
        
        :raises ValueError: If split lengths are invalid or if no cropped segment has valid size
        
        :return: Returns nothing, all images are saved to image_directory
        :rtype: None
        """
        #create temporary directory to save cropped images
        cropped_image_directory = os.path.join(image_directory, "cropped_images") 
        os.makedirs(cropped_image_directory, exist_ok=True)
        
        image_path = os.path.join(image_directory, f"{image_name}.png")
        image = cv2.imread(image_path)

        if image is None:
            print(f"Error: Image {image_name}.png not found.")
            return
        
        # Set parameters
        threshold = 254.8
        percentage_threshold = 0.995
        step_size = 10

        # Find the first split line within the first 1/4 of the image (usually the reaction diagram)
        region_start_1 = int(1/4 * len(image))
        region_end_1 = int(3/8 *len(image))
        first_split_line = _find_split_line(image, threshold, region_start_1, region_end_1, percentage_threshold, step_size)

        try: 
            # Find adaptive split lines based on the remaining height after the first split line
            split_lines = _adaptive_split_lines(image, first_split_line, min_segment_height, threshold, percentage_threshold, step_size)

            # Check if split lines are valid
            if len(split_lines) < 1:
                raise ValueError(f"Error: Unable to find valid split lines for {image_name}. Saving original image.")

            # Crop the image into segments
            segments = _segment_image(image, split_lines)

            # Check if cropped segments have valid size
            valid_segments = 0
            for idx, segment in enumerate(segments): 
                if segment.size > 0:
                    cv2.imwrite(os.path.join(cropped_image_directory, f"{image_name}_{idx+1}.png"), segment)
                    valid_segments += 1
                else: 
                    print(f"Warning: Segment {idx+1} of {image_name} has zero size. Skipping.")
            
            if valid_segments == 0:
                raise ValueError(f"Error: No valid segments for {image_name}. Saving original image.")

        except Exception as e: 
            print(str(e))
            cv2.imwrite(os.path.join(cropped_image_directory, f"{image_name}_original.png"), image)

    
def batch_crop_image(image_directory:str, min_segment_height:float=120):
    """
    Crop all images in a given directory 

    :param image_directory: Directory of images to crop
    :type image_directory: str
    :param min_segment_height: minimum height of each segment, defaults to 120
    :type min_segment_height: float
    
    :return: Returns nothing, all images are saved in image_directory
    :rtype: None
    """
    
    # Create a directory to save the cropped segments
    cropped_image_directory = os.path.join(image_directory, "cropped_images")
    os.makedirs(cropped_image_directory, exist_ok=True)

    for file in os.listdir(image_directory):
        if (file.endswith('.png')):
            image_name = file.removesuffix('.png')
            crop_image(image_name, image_directory, min_segment_height)