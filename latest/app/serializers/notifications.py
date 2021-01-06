

from rest_framework import serializers

from app.models.notifications import Notification
from app.serializers.user import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    created_for = serializers.SerializerMethodField()
    req_data = serializers.JSONField()

    class Meta:
        model = Notification
        fields = ('id', 'title','description',"created_on",'created_by','created_for','req_data','type')

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by,context={"request":self.context.get("request")}).data

    def get_created_for(self, obj):
        return UserSerializer(obj.created_for,context={"request":self.context.get("request")}).data



