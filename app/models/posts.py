from tortoise import fields, models


class Post(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=128, unique=True)
    body = fields.TextField()
    toc = fields.TextField(null=True)
    description = fields.TextField(null=True)
    source = fields.TextField(null=True)
    slug = fields.CharField(max_length=64)
    read_time = fields.CharField(max_length=64)
    timestamp = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
