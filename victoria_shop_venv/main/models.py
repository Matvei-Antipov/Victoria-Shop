from django.db import models

#goods
class Goods(models.Model):
    name = models.CharField(("name"), max_length=50)
    description = models.CharField(("description"), max_length=288)
    price = models.IntegerField(("price"))
    status = models.BooleanField(("status"))
    article = models.IntegerField(("article"))
    category = models.CharField(("category"), max_length=50)
    country = models.CharField(("country"), max_length=50)
    base64_data = models.TextField(("base64_data"))

    class Meta:
        managed = False
        db_table = 'goods'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

#product
class Product(models.Model):
    name = models.CharField(("name"), max_length=50)
    description = models.CharField(("description"), max_length=288)
    price = models.IntegerField(("price"))
    status = models.BooleanField(("status"))
    article = models.IntegerField(("article"))
    category = models.CharField(("category"), max_length=50)
    country = models.CharField(("country"), max_length=50)
    base64_data = models.TextField(("base64_data"))

    class Meta:
        managed = False
        db_table = 'goods'