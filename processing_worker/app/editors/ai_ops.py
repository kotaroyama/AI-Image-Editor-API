from PIL import Image
from rembg import remove, new_session

print("Loading rembg AI model into memory")
AI_SESSION = new_session("u2net")

def rembg_process_image(local_input, local_output):
    with Image.open(local_input) as img:
        processed_img = remove(img, session=AI_SESSION)
        processed_img.save(local_output, format="PNG")