from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Judge
from participant.serializers import UserSerializer

class JudgeSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Judge
        fields = ('id', 'user', 'title')

    def get_user(self, obj):
        return UserSerializer(obj.user).data