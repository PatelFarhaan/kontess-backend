from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

import json
from .models import Participant, TeamRequest
from team.serializers import TeamSerializer

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(min_length=8)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'], 
            password=validated_data['password'], 
            first_name=validated_data["first_name"], 
            last_name=validated_data["last_name"]
        )
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name')


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
        fields = ('id', 'user','graduation_year', 'team')

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