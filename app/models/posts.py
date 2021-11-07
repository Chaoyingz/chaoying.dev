from typing import Any

from tortoise import fields, models


class Topic(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, unique=True)

    def __str__(self) -> Any:
        return self.name


class Post(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128, unique=True)
    body = fields.TextField()
    toc = fields.TextField(null=True)
    description = fields.TextField(null=True)
    source = fields.TextField(null=True)
    slug = fields.CharField(max_length=64)
    read_time = fields.CharField(max_length=64)
    topics = fields.ManyToManyField("models.Topic", related_name="posts", null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
