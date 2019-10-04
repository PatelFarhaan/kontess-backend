from rest_framework import serializers
from rest_framework.validators import UniqueValidator

import json
from app.models.participant import Participant, TeamRequest
from app.serializers.user import UserSerializer
from app.serializers.team import TeamSerializer


class TeamRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRequest
        fields = ('id', 'essay', 'team', 'participant')


class ParticipantBasicSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Participant
        fields = ('id', 'user')

    def get_user(self, obj):
        return UserSerializer(obj.user).data

class ParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ('id', 'user','title', 'team')

    def get_user(self, obj):
        return UserSerializer(obj.user).data

    def get_team(self, obj):
        if(obj.team):
            return TeamSerializer(obj.team).data
        return json.dumps({})

    def get_team_requests(self, obj):
        if(obj.team):
            return TeamSerializer(obj.team).data
        return json.dumps({})