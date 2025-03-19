from src.schemas.comments import CommentSchema
from src.utils.repository import AbstractRepository


class CommentsService:
    def __init__(self, comments_repo: AbstractRepository):
        self.comments_repo: AbstractRepository = comments_repo

    async def add_comment(self, comment: CommentSchema):
        comments_dict = comment.model_dump()
        comment_id = await self.comments_repo.add_one(comments_dict)
        return comment_id

    async def get_comments(self):
        tasks = await self.comments_repo.find_all()
        return tasks