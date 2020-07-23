

from rest_framework import serializers

from app.models.organizer import Organizer
from app.serializers.user import UserSerializer

class OrganizerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Organizer
        fields = ('id', 'user')

    def get_user(self, obj):
        return UserSerializer(obj.user,context={"request":self.context.get("request")}).data