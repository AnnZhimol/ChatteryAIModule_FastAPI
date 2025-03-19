from typing import Optional

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.enums.filter_class_mood import FilterClassMood
from src.enums.filter_class_type import FilterClassType
from src.schemas.comments import CommentSchema

from src.db.db import Base


class Comments(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str]
    content: Mapped[str]
    filter_class_mood: Mapped[int] = mapped_column(Enum(FilterClassMood))
    filter_class_type: Mapped[int] = mapped_column(Enum(FilterClassType))
    parent_author: Mapped[Optional[str]]
    parent_content: Mapped[Optional[str]]
    create_date: Mapped[int]
    translation_url: Mapped[str]
    user_id: Mapped[int]

    def to_read_model(self) -> CommentSchema:
        return CommentSchema(
            id=self.id,
            author=self.author,
            content=self.content,
            filter_class_mood=self.filter_class_mood,
            filter_class_type=self.filter_class_type,
            parent_author=self.parent_author,
            parent_content=self.parent_content,
            create_date=self.create_date,
            translation_url=self.translation_url,
            user_id=self.user_id,
        )
