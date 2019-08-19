from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from participant.models import Participant, TeamRequest
from .models import Team
import participant.serializers

class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=Team.objects.all())]
    )
    description = serializers.CharField(max_length=100)
    requests = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    def create(self, validated_data):
        team = Team.objects.create(
            name=validated_data['name'], 
            description=validated_data['description']
        )
        return team

    class Meta:
        model = Team
        fields = ('id', 'name','description', 'requests', 'participants')
        
    def get_requests(self, obj):
        teamrequests = TeamRequest.objects.filter(team=obj)
        return participant.serializers.TeamRequestSerializer(teamrequests, many=True).data

    def get_participants(self, obj):
        participants = Participant.objects.filter(team=obj)
        return participant.serializers.ParticipantBasicSerializer(participants, many=True).data