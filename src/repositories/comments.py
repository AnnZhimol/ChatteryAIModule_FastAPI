from src.models.comments import Comments
from src.utils.repository import SQLAlchemyRepository


class CommentsRepository(SQLAlchemyRepository):
    model = Comments