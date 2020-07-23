

import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.forms.models import model_to_dict

from app.models.participant import TeamRequest
from app.models.judge import TeamMentorRequest
from app.models.team import Team,TeamPortfolio,TeamTrack,Invitation,TeamEvent,TeamTask,TeamDocs,TeamTaskStatus
from app.models.user import User
from app.models.task import ParticipantTask,Task,TaskGrading,TaskGrades
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
    partipants = ParticipantDetailSerializer(many=True,allow_null=True,required=False)
    created_by = UserSerializer(allow_null=True,required=False)
    team_mentor = UserSerializer(allow_null=True,required=False)
    
    class Meta:
        model=TeamEvent
        fields = ("id","title","location","partipants","schedule_date","created_by","created_on","team_mentor")
        read_only_fields=("created_on","created_by","team_mentor") 

class TeamTaskStatusSerializer(serializers.ModelSerializer):
    participant = ParticipantDetailSerializer(allow_null=True,required=False)
    class Meta:
        model = TeamTaskStatus
        fields = ("id","team_task","status","participant","created_on","updated_on")
        read_only_fields=("created_on","updated_on") 

class TeamTaskSerializer(serializers.ModelSerializer):
    participants = ParticipantDetailSerializer(many=True,allow_null=True,required=False)
    created_by = UserSerializer(allow_null=True,required=False)
    class Meta:
        model = TeamTask
        fields = ("id","title","description","dead_line","participants","created_on","created_by")
        read_only_fields=("created_on","created_by","participants") 
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        task_status = TeamTaskStatus.objects.filter(team_task=instance,participant__user=request.user)
        if task_status:
            task_status = task_status[0]
            data["task_status"] = TeamTaskStatusSerializer(task_status,context=self.context).data
        
        return data
        
        
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
    team_lead = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ('id', 'name', 'logo', 'description','portfolio',"partipants","team_mentor","created_by","team_track","docs","team_lead")
        read_only_fields = ('id','created_by','team_mentor','partipants',"team_track","docs","team_lead")

    def get_team_mentor(self, obj):
        return UserSerializer(obj.team_mentor,context={"request":self.context.get("request")}).data if obj.team_mentor else {}

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by,context={"request":self.context.get("request")}).data if obj.created_by else {} 
    
    def get_team_lead(self, obj):
        return UserSerializer(obj.team_lead,context={"request":self.context.get("request")}).data if obj.team_lead else {}
    
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
            
        if instance.team_mentor:    
            data["team_mentor"]["judge_status"] = "approved"
            data["team_mentor"]["admin_status"] = "approved" 
        #if request.user.is_superuser:
        mentor_request = TeamMentorRequest.objects.filter(team=instance).order_by("-id")
        if mentor_request:
            mentor_request = mentor_request[0]
            if mentor_request.admin_status != "rejected" and mentor_request.judge_status != "rejected":
                data["team_mentor"] = UserSerializer(mentor_request.for_judge,context={"request":self.context.get("request")}).data if mentor_request else {} 
                data["team_mentor"]["judge_status"] = mentor_request.judge_status if mentor_request else None
                data["team_mentor"]["admin_status"] = mentor_request.admin_status if mentor_request else None
   
        return data
        
class TeamAdminTaskSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(max_length=100)
    portfolio = TeamPortfolioSerializer(many=True,allow_null=True,required=False)
    partipants = ParticipantDetailSerializer(many=True,allow_null=True,required=False)
    team_mentor = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    team_track = TeamTrackSerializer(required=False,allow_null=True)
    docs = TeamDocsSerializer(required=False,allow_null=True,many=True)
    team_lead = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ('id', 'name', 'logo', 'description','portfolio',"partipants","team_mentor","created_by","team_track","docs","team_lead")
        read_only_fields = ('id','created_by','team_mentor','partipants',"team_track","docs","team_lead")

    def get_team_mentor(self, obj):
        return UserSerializer(obj.team_mentor,context={"request":self.context.get("request")}).data if obj.team_mentor else {}

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by,context={"request":self.context.get("request")}).data if obj.created_by else {} 
    
    def get_team_lead(self, obj):
        return UserSerializer(obj.team_lead,context={"request":self.context.get("request")}).data if obj.team_lead else {}
    
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        participants = instance.partipants
        request = self.context.get("request")
        
        try:
            task = ParticipantTask.objects.get(team=instance,task_id=request.query_params.get("task_id"))
        except Exception as e:
            task = None
            
        if task:
            data["submitted_task_id"] = task.id
            data["submitted_by"] = UserSerializer(task.submitted_by,context={"request":self.context.get("request")}).data if task.submitted_by else None
            data["submitted_docs"]= [{"id":t.id,"doc":request.build_absolute_uri(t.doc.url) if t.doc else None } for t in task.submitted_docs.all()]
        else:
            data["submitted_task_id"]=None
            data["submitted_by"] = None
            data["submitted_docs"] = []
        if request.user.is_judge:
            _grades = TaskGrading.objects.filter(task=self.context.get("task"),team=instance,judge=request.user)
        else:
            _grades = TaskGrading.objects.filter(task=self.context.get("task"),team=instance)
        data["task_grading"] = []
        if _grades:
            
            for grade in _grades:
                dt={
                    "id":grade.id,
                    "over_all_comments":grade.over_all_comments,
                    "status":grade.status,
                    "judge":UserSerializer(grade.judge,context={"request":self.context.get("request")}).data if task.submitted_by else None,
                    "grades":[]
                }
                for i in TaskGrades.objects.filter(grade=grade):
                    dt["grades"].append({
                        "id":i.id,
                        "score":i.score,
                        "comment":i.comment,
                        "questions":model_to_dict(i.questions) if i.questions else {}
                    }) 
                data["task_grading"].append(dt)
        return data 
    
    
class TeamTaskDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(allow_null=True,required=False)
    class Meta:
        model = TeamTask
        fields = ("id","title","description","dead_line","created_on","created_by")

class TeamDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(max_length=100)
    created_by = UserSerializer(allow_null=True,required=False)
    class Meta:
        model = Team
        fields = "__all__"
        
class TeamTaskDetailStatusSerializer(serializers.ModelSerializer):
    participant = ParticipantDetailSerializer(allow_null=True,required=False)
    team_task = TeamTaskDetailSerializer(allow_null=True,required=False)
    team = TeamDetailSerializer(allow_null=True,required=False)
    class Meta:
        model = TeamTaskStatus
        fields = ("id","team_task","team","status","participant","created_on","updated_on")
        read_only_fields=("created_on","updated_on")        