from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)
