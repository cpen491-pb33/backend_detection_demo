from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
import ee
import geemap
from .models import Detection
from .serializers import GeoCoordinatesSerializer, DetectionSerializer

# Create your views here.
class DetectionView(APIView):
    def post(self, request, format=None):
        geo_serializer = GeoCoordinatesSerializer(data=request.data)
        if geo_serializer.is_valid():
            lng = geo_serializer.data.get('lng')
            lat = geo_serializer.data.get('lat')

            class_values, class_names, class_palette = self.supervised_learning(lng, lat)

            detection = Detection(class_values, class_names, class_palette)

            return Response(DetectionSerializer(detection).data, status=status.HTTP_200_OK)

        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)

    def supervised_learning(self, lng, lat):
        Map = geemap.Map()

        point = ee.Geometry.Point([float(lng), float(lat)])

        # It's a real time image collection and updates to the current date
        imageCollection = 'LANDSAT/LC08/C01/T1_RT'
        dates = ['2020-01-01', '2020-12-31']
        min, max, bands = 0, 30000, ['B4', 'B3', 'B2']

        image = ee.ImageCollection(imageCollection) \
            .filterBounds(point) \
            .filterDate(dates[0], dates[1]) \
            .sort('CLOUD_COVER') \
            .first() \
            .select('B[1-7]')
        # .filterBounds(geo_area) \

        vis_params = {
            'min': min,
            'max': max,
            'bands': bands
        }

        Map.centerObject(point, 8)
        Map.addLayer(image, vis_params, "Landsat-8")

        imageDate = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        print('imageDate', imageDate)
        imageInfo = image.get('CLOUD_COVER').getInfo()
        print('imageInfo', imageInfo)

        # Add labelling
        nlcd = ee.Image('USGS/NLCD/NLCD2016').select('landcover').clip(image.geometry())
        Map.addLayer(nlcd, {}, 'NLCD')

        # Make the training dataset.
        points = nlcd.sample(**{
            'region': image.geometry(),
            'scale': 30,
            'numPixels': 5000,
            'seed': 0,
            'geometries': True  # Set this to False to ignore geometries
        })

        Map.addLayer(points, {}, 'training', False)

        print('points size', points.size().getInfo())
        print('points info', points.first().getInfo())

        # Use these bands for prediction.
        bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']

        # This property of the table stores the land cover labels.
        label = 'landcover'

        # Overlay the points on the imagery to get training.
        training = image.select(bands).sampleRegions(**{
            'collection': points,
            'properties': [label],
            'scale': 30
        })

        # Train a CART classifier with default parameters.
        trained = ee.Classifier.smileCart().train(training, label, bands)

        print('training data info', training.first().getInfo())

        # Classify the image with the same bands used for training.
        result = image.select(bands).classify(trained)

        # # Display the clusters with random colors.
        Map.addLayer(result.randomVisualizer(), {}, 'classfied')

        class_palette = nlcd.get('landcover_class_palette').getInfo()
        print('class palette', class_palette)
        class_values = nlcd.get('landcover_class_values').getInfo()
        print('class values', class_values)
        class_names = nlcd.get('landcover_class_names').getInfo()
        for i, name in enumerate(class_names):
            class_names[i] = name.split('-')[0].strip()
        print('class names', class_names)

        return class_values, class_names, class_palette