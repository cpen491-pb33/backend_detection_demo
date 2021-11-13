from rest_framework import serializers
from .models import GeoCoordinates, Detection

class GeoCoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoCoordinates
        fields = ('lng', 'lat')

# I only tried to return the elements in the legend, should add the image later
class DetectionSerializer(serializers.Serializer):    
    class_values = serializers.ListField(
        child=serializers.IntegerField()
    )
    class_names = serializers.ListField(
        child=serializers.CharField()
    )
    class_palette = serializers.ListField(
        child=serializers.CharField()
    )