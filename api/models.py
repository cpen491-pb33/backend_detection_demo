from django.db import models
from rest_framework import serializers

# Create your models here.
class GeoCoordinates(models.Model):
    lng = models.DecimalField(max_digits=20, decimal_places=15)
    lat = models.DecimalField(max_digits=20, decimal_places=15)

class Detection(models.Model):
    def __init__(self, class_values, class_names, class_palette):
        self.class_values = class_values
        self.class_names = class_names
        self.class_palette = class_palette
