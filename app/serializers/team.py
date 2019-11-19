'''
/**
 *@copyright : ToXSL Technologies Pvt. Ltd. < www.toxsl.com >
 *@author     : Shiv Charan Panjeta < shiv@toxsl.com >
 *
 * All Rights Reserved.
 * Proprietary and confidential :  All information contained herein is, and remains
 * the property of ToXSL Technologies Pvt. Ltd. and its partners.
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 *
 *
 */
'''

import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from app.models.participant import TeamRequest
from app.models.team import Team,TeamPortfolio,TeamTrack,Invitation,TeamEvent,TeamTask,TeamDocs
from app.models.user import User
from app.serializers.participant import ParticipantDetailSerializer,TeamRequestDetailSerializer
from app.serializers.user import UserSerializer


class TeamTrackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= TeamTrack
        fields = ("id","track_name","description","slug")
        read_only_fields = ("id","slug")

class TeamPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model=TeamPortfolio
        fields=("id","docs")

class TeamEventSerializer(serializers.ModelSerializer):
    class Meta:
        model=TeamEvent
        fields = ("id","title","description","schedule_date","created_on")
        read_only_fields=("created_on",) 

class TeamTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamTask
        fields = ("id","title","description","dead_line","created_on")
        read_only_fields=("created_on",) 
        
class TeamDocsSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    doc = serializers.FileField()
    class Meta:
        model = TeamDocs
        fields = ("id","doc_name","doc","created_on","created_by","team")
        read_only_fields=("created_on","created_by","team") 

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by,context={"request":self.context.get("request")}).data if obj.created_by else {} 
    
    
    
class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(max_length=100)
    portfolio = TeamPortfolioSerializer(many=True,allow_null=True,required=False)
    partipants = ParticipantDetailSerializer(many=True,allow_null=True,required=False)
    team_mentor = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    team_track = TeamTrackSerializer(required=False,allow_null=True)
    docs = TeamDocsSerializer(required=False,allow_null=True,many=True)
    task = TeamTaskSerializer(required=False,allow_null=True,many=True)
    event = TeamEventSerializer(required=False,allow_null=True,many=True)
    
    class Meta:
        model = Team
        fields = ('id', 'name', 'logo', 'description','portfolio',"partipants","team_mentor","created_by","team_track","docs","task","event")
        read_only_fields = ('id','created_by','team_mentor','partipants',"team_track","docs","task","event")

    def get_team_mentor(self, obj):
        return UserSerializer(obj.team_mentor,context={"request":self.context.get("request")}).data if obj.team_mentor else {}

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by,context={"request":self.context.get("request")}).data if obj.created_by else {} 

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        team_request = TeamRequest.objects.filter(team=instance,participant__user=request.user)
        if team_request:
            if team_request[0].status == 'rejected':
                data["status"] = None
            else:
                data["status"] = team_request[0].status
        else:
            data["status"] = None
        return data
        
