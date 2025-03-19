from pydantic import BaseModel
from typing import Optional

from src.enums.filter_class_mood import FilterClassMood
from src.enums.filter_class_type import FilterClassType


class CommentSchema(BaseModel):
    id: int
    author: str
    content: str
    filter_class_mood: FilterClassMood
    filter_class_type: FilterClassType
    parent_author: Optional[str] = None
    parent_content: Optional[str] = None
    create_date: int
    translation_url: str
    user_id: int

    class Config:
        from_attributes = True