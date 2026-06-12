from typing import List, Dict, Any

def get_detected_objects(
    results,
    confidence_threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Decodes raw Ultralytics YOLO inference results into a structured list
    suitable for PostgreSQL JSONB storage.
    """
    if not results:
        return []

    first_result = results[0]

    # Grab the dictionary mapping class IDs to names (e.g., {0: 'person', 16: 'dog'})
    class_names = first_result.names
    detected_objects = []

    # Loop through every single bouding box detected in the image
    for box in first_result.boxes:
        class_id = int(box.cls[0].item())
        label = class_names[class_id]
        confidence = float(box.conf[0].item())

        # Extract coordinates [xmin, ymin, xmax, ymax]
        coords = box.xyxy[0].tolist()

        # Only keep detections the model is reasonably confident about
        if confidence > confidence_threshold:
            detected_objects.append({
                "object": label,
                "confidence": round(confidence, 2),
                "bounding_box": [round(c, 1) for c in coords]
            })

    return detected_objects
    