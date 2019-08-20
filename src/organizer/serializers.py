from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Organizer
from participant.serializers import UserSerializer

class OrganizerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Organizer
        fields = ('id', 'user')

    def get_user(self, obj):
        return UserSerializer(obj.user).data