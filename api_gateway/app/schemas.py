from pydantic import BaseModel

class EditRequest(BaseModel):
    image_id: str
    action: str