from rest_framework import serializers
from .models import (
    Application, Organization, Configuration
)

class ApplicationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__' 
        

class ApplicationReadSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = Application
        fields = '__all__' 
        



class OrganizationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__' 
        

class OrganizationReadSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = Organization
        fields = '__all__' 
        

class ConfigurationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = '__all__' 
        

class ConfigurationReadSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = Configuration
        fields = '__all__' 
        
