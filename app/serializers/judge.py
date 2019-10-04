from rest_framework import serializers

from app.models.judge import Judge
from app.serializers.user import UserSerializer

class JudgeSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Judge
        fields = ('id', 'user', 'title')

    def get_user(self, obj):
        return UserSerializer(obj.user).data