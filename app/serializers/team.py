import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


from app.models.team import Team
from app.models.user import User
# from app.serializers.participant import ParticipantSerializer


class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(max_length=100)

    class Meta:
        model = Team
        fields = ('id', 'name', 'description')
        read_only_fields = ('id','created_by')


class TeamRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'essay', 'team', 'participant')
