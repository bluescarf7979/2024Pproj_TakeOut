from rest_framework import serializers
from .models import RoadInfo

class RoadInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadInfo
        fields = '__all__'
