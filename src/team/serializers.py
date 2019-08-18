from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import Participant


class TeamSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = ('user','graduation_year', 'team')

    # def get_user(self, obj):
        # return UserSerializer(obj.user).data