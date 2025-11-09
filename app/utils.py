import uuid
from typing import Tuple

def new_ids(user_id: str) -> Tuple[str, str]:
    image_id = str(uuid.uuid4())
    object_key = f"images/{user_id}/{image_id}"
    return image_id, object_key
