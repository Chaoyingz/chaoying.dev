from datetime import datetime

from tortoise import fields, models


class Post(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128)
    body = fields.TextField()
    timestamp = fields.DatetimeField(default=datetime.now)

    def __str__(self) -> str:
        return f"Post {self.id}: {self.title}"
