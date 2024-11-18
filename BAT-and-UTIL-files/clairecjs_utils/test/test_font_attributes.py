from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

# Function to create a random pixel background
def create_random_background(width, height):
    data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(data, 'RGB')

# Function to draw text with different effects
def draw_text_examples(image, font_path):
    d = ImageDraw.Draw(image)
    width, height = image.size
    font = ImageFont.truetype(font_path, 40)

    # Define text and colors
    text = "Text Example"
    font_color = (0, 255, 0)  # green text
    shadow_color = (0, 0, 0)  # black shadow
    box_color = (0, 0, 0, 128)  # semi-transparent black box

    # Shadow Example 1
    shadow_image = image.copy()
    d = ImageDraw.Draw(shadow_image)
    d.text((10 + 2, 10 + 2), text, font=font, fill=shadow_color)
    d.text((10, 10), text, font=font, fill=font_color)
    shadow_image.save('text_shadow_1.png')

    # Shadow Example
    shadow_image = image.copy()
    d = ImageDraw.Draw(shadow_image)
    d.text((10 + 2, 10 + 2), text, font=font, fill=shadow_color)
    d.text((10,     10),     text, font=font, fill=  font_color)
    shadow_image.save('text_shadow_2.png')

    # Shadow Example
    shadow_image = image.copy()
    d = ImageDraw.Draw(shadow_image)
    d.text((10 + 20, 10 + 20), text, font=font, fill=shadow_color)
    d.text((10,      10),     text, font=font, fill=  font_color)
    shadow_image.save('text_shadow_3.png')

    # Background Box Example
    if False:
        box_image = image.copy()
        d = ImageDraw.Draw(box_image)
        text_bbox = d.textbbox((10, 10), text, font=font)
        d.rectangle(text_bbox, fill=box_color)
        d.text((10, 10), text, font=font, fill=font_color)
        box_image.save('text_background_box.png')

    # Contrast Adjustment Example
    contrast_image = image.copy()
    enhancer = ImageEnhance.Contrast(contrast_image)
    #ontrast_image = enhancer.enhance(2.0)
    contrast_image = enhancer.enhance(0.5)
    d = ImageDraw.Draw(contrast_image)
    d.text((10, 10), text, font=font, fill=font_color)
    contrast_image.save('text_contrast.png')

    # Blur Example
    blur_image = image.copy()
    blur_image = blur_image.filter(ImageFilter.GaussianBlur(radius=2))
    d = ImageDraw.Draw(blur_image)
    d.text((10, 10), text, font=font, fill=font_color)
    blur_image.save('text_blur.png')

    # Blur Example
    blur_image = image.copy()
    blur_image = blur_image.filter(ImageFilter.GaussianBlur(radius=1))
    d = ImageDraw.Draw(blur_image)
    d.text((10, 10), text, font=font, fill=font_color)
    blur_image.save('text_blur_2.png')


    # Color Manipulation Example
    if False:
        color_image = image.copy()
        d = ImageDraw.Draw(color_image)
        d.text((10, 10), text, font=font, fill=(255, 0, 0))  # red text color
        color_image.save('text_color.png')

    # Edge Detection Example
    if False:
        edges_image = image.convert('L').filter(ImageFilter.FIND_EDGES)
        d = ImageDraw.Draw(edges_image)
        #.text((10, 10), text, font=font, fill=font_color)
        d.text((10, 10), text, font=font, fill=1)
        edges_image.save('text_edges.png')


def find_first_ttf_file(start_dir):
    """
    Searches for the first .ttf file starting from the given directory,
    then searches in subdirectories and parent directories.

    Args:
        start_dir (str): The directory to start the search from.

    Returns:
        str: The path of the first .ttf file found, or None if no file is found.
    """
    # Search in current directory and subdirectories
    import os
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.lower().endswith('.ttf'):
                ttf_path = os.path.join(root, file)
                print(f"Found .ttf file: {ttf_path}")
                return ttf_path

    # Search in parent directories
    parent_dir = start_dir
    while True:
        parent_dir = os.path.dirname(parent_dir)
        if parent_dir == os.path.dirname(parent_dir):  # root directory
            break
        for root, dirs, files in os.walk(parent_dir):
            for file in files:
                if file.lower().endswith('.ttf'):
                    ttf_path = os.path.join(root, file)
                    print(f"Found .ttf file: {ttf_path}")
                    return ttf_path
    print("No .ttf file found.")
    return None


# Main script
def main():
    width, height = 800, 480
    import os
    #ont_path = "arial.ttf"  # Ensure this font file is in your working directory
    font_path = find_first_ttf_file(os.getcwd())
    if not font_path: print("Please provide a valid .ttf file.")
    else:             print(f"Using font file: {font_path}")


    # Create a random background image
    background = create_random_background(width, height)
    background.save('random_background.png')

    # Draw text examples
    draw_text_examples(background, font_path)

if __name__ == '__main__':
    main()
