from datetime import datetime

from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)


class Post(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128)
    body = fields.TextField()
    slug = fields.CharField(max_length=64)
    timestamp = fields.DatetimeField(default=datetime.now)
