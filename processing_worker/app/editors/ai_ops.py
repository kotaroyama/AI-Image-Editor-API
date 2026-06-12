from PIL import Image
from rembg import remove, new_session
from ultralytics import YOLO

print("Loading rembg AI model into memory")
AI_SESSION = new_session("u2net")

def rembg_process_image(local_input, local_output):
    with Image.open(local_input) as img:
        processed_img = remove(img, session=AI_SESSION)
        processed_img.save(local_output, format="PNG")

def yolo_process_image(local_input, local_output):
    model = YOLO('yolov8n.pt')
    results = model(local_input)
    first_result = results[0]

    rendered_image_bgr = first_result.plot()
    rendered_image_rgb = rendered_image_bgr[..., ::-1]
    Image.fromarray(rendered_image_rgb).save(local_output)