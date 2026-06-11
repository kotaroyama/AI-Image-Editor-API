from PIL import Image

def grayscale_process_image(local_input, local_output):
    with Image.open(local_input) as img:
        processed_img = img.convert("L")
        processed_img.save(local_output)