

from rest_framework import serializers

from app.models.events import Events,EventLogs
from app.serializers.user import UserSerializer



class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.CurrentUserDefault()
    class Meta:
        model = Events
        fields = "__all__"
        read_only_fields = ("created_on","created_by")



class EventLogSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(required=False,allow_null=True)
    created_for = UserSerializer(required=False,allow_null=True)
    event = EventSerializer(required=False,allow_null=True)

    class Meta:
        model = EventLogs
        fields = "__all__"
        read_only_fields = ("created_on","created_by","created_for")

