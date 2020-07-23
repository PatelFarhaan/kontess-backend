
import json
from datetime import datetime,date
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route,action
from django_filters.rest_framework import DjangoFilterBackend

from app.models.user import LinkExpiration
from app.models.team import Team,TeamPortfolio,TeamTrack,Invitation,TeamEvent,TeamTask,TeamDocs,TeamTaskStatus
from app.models.judge import TeamMentorRequest,JudgeRequestTeam
from app.models.participant import Participant, TeamRequest
from app.models.task import AssingJudgeToTask ,Task,ParticipantTask,TaskLock,RandomJudgeToTaskAndTeam
from app.serializers.team import TeamSerializer,TeamTrackSerializer,TeamEventSerializer,TeamTaskSerializer,TeamDocsSerializer,TeamTaskStatusSerializer,TeamAdminTaskSerializer,TeamTaskDetailStatusSerializer
from app.serializers.task import ParticipantTaskSerializer
from app.serializers.user import UserSerializer
from django.forms.models import model_to_dict
from app.backends.team_filters import TeamFilter,TeamDocsFilter

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from app.views.notifications import create_notification
from app.models.notifications import Notification
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.functions import Cast
from django.db.models.fields import DateField

from django.core.mail import EmailMultiAlternatives

User = get_user_model()

class ContestBaseViewSet(viewsets.ModelViewSet):
    def get_data(self):
        return {}

    def perform_create(self, serializer):
        serializer.save(**self.get_data())

class TeamViewSet(ContestBaseViewSet):
    """
    team/
    """
    serializer_class = TeamSerializer
    permission_classes_by_action = {'create': [permissions.IsAuthenticated],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'accept_team_request': [permissions.IsAuthenticated],
                                    'reject_team_request': [permissions.IsAuthenticated]}
    
    filter_backends = (DjangoFilterBackend, )
    filter_class = TeamFilter
    
    total_members = 6
    if_count = 0
    
    myteam = None
    participant = None
    
    def get_queryset(self):
        teams = Team.objects.all()
        user_teams = teams.filter(Q(team_lead = self.request.user)|Q(created_by = self.request.user))
        my_teams = user_teams
        
        if not self.request.user.is_superuser:
            self.participant = Participant.objects.filter(user=self.request.user)
            _teams = Team.objects.filter(partipants__in = self.participant)
            my_teams = user_teams | _teams
            
        if self.request.query_params.get("name",None):
           teams = teams.filter(name__icontains=self.request.query_params.get("name"))
           
        if self.request.query_params.get("track",None):
            track = TeamTrack.objects.get(slug=self.request.query_params.get("track"))
            return teams.filter(team_track=track).difference(my_teams).order_by('-id') 
        return teams.difference(my_teams).order_by('-id') 
    
  
    def retrieve(self, request, *args, **kwargs):
        instance = Team.objects.get(id=kwargs.get('pk'))
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_data(self):
        return {'created_by': self.request.user}

    def create(self, request, *args, **kwargs):
        data = request.data
        data = {"name":data.get("name"),"logo":data.get('logo',None),"description":data.get("description") if data.get("description") else "" }
        team = Team.objects.filter(created_by=request.user,name=data.get("name"))
        if team:
            return Response({"msg":"Team already exist with same name.","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
        
        track = TeamTrack.objects.filter(slug=request.data.get("team_track",None))
        if not track:
            return Response({"msg":"Please select a team track for this team","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        track = track[0]
        
        team = Team.objects.create(created_by=request.user,team_track=track,**data)                   
        if request.user.is_participant:
            team.partipants.add(Participant.objects.get(user=request.user))
            team.team_lead=request.user
            team.save()
            
        if request.data.get("portfolio",[]):
            portfolio=request.data.pop("portfolio")
            for _docs in portfolio:
                try:
                    TeamPortfolio.objects.get(docs=_docs,team=team)
                except TeamPortfolio.DoesNotExist:
                    TeamPortfolio.objects.create(docs=_docs,team=team)
        dt = self.get_serializer(team).data
        dt.update({"members_count":len(team.partipants.all())})   
        data={
            "status":status.HTTP_200_OK,
            "data":dt
        }
        return Response(data,status=status.HTTP_200_OK)
    
    @detail_route(methods=['post'])
    def team_update(self,request,pk=None):
        team = get_object_or_404(Team, pk=pk)
        
        data = request.data
        data = {"name":data.get("name"),"description":data.get("description") if data.get("description") else "" }
        if request.data.get('logo',None):
            data.update({"logo":request.data.get('logo',None)})
            
        if team.name.lower() != data.get("name").lower():
            if Team.objects.filter(name=data.get("name"),description=data.get("description")):
                data={
                        "status":status.HTTP_409_CONFLICT,
                        "msg": "Team already exist with same name and description."
                    }
                return Response(data,status=status.HTTP_409_CONFLICT)
            
            if Team.objects.filter(name=data.get("name")):
                data={
                        "status":status.HTTP_409_CONFLICT,
                        "msg": "Team is already exist with same name."
                    }
                return Response(data,status=status.HTTP_409_CONFLICT)
        
        
        track = TeamTrack.objects.filter(slug=request.data.get("team_track",None))
        if not track:
            return Response({"msg":"Please select a team track for this team","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        track = track[0]
        
        for attr, value in data.items(): 
            setattr(team, attr, value)
        team.team_track=track
        team.save()
        
        if request.data.get("deletedItems",[]):
            _team_portfolio = TeamPortfolio.objects.filter(id__in=request.data.get("deletedItems").split(','))
            _team_portfolio.delete()
        
        
        if request.data.get("portfolio",[]):
            portfolio = request.data.pop("portfolio")           
            for _docs in portfolio:
                try:
                    TeamPortfolio.objects.get(docs=_docs,team=team)
                except TeamPortfolio.DoesNotExist:
                    TeamPortfolio.objects.create(docs=_docs,team=team)
        data={
            "status":status.HTTP_200_OK,
            "data":self.get_serializer(team).data
        }
        
        return Response(data,status=status.HTTP_200_OK)
        
    @detail_route(methods=['post'])
    def send_invitation(self,request,pk=None):
        participants=request.data.get("participants")
        if not participants:
            return Response({"status":status.HTTP_400_BAD_REQUEST,"msg":"Please select participant"},status=status.HTTP_200_OK)
        
        team = get_object_or_404(Team, pk=pk)
        users = User.objects.filter(id__in=[participant.get("id") for participant in participants])
        participants = Participant.objects.filter(user__in=users)
        team_owner = team.created_by.email
        mail_subject = "Invitations to join team '{}'".format(team.name)
        for participant in participants:
            msg="Dear {},\n You have been invited to join team {}. To join,Please click on the link {}".format(
                participant.user.full_name,team.name,settings.INVITE_URL.format(team.id,participant.user.id)
            )
            LinkExpiration.objects.create(url=settings.INVITE_URL.format(team.id,participant.user.id))
            invitation = Invitation.objects.create(participants=participant,team=team,status="pending",created_by=request.user)
            request
            email = EmailMultiAlternatives(mail_subject, body=msg, to=[participant.user.email], from_email=team_owner)
            email.send()
            
            invitation.email_send = True
            invitation.save()
            data={
             "title":"Invitation to join team <strong><a href='/dashboard/team_view/{0}'>'{1}'</a></strong>".format(team.id,team.name),
             "description":"team invitation",
             "type":"invitation",
             "created_for":participant.user,
             "req_data":{"team_id":team.id,"user_id":participant.user.id}   
            }
            create_notification(data,request)
            if participant.user.invited_join_request:
                try:
                    html_message="<html><body>Invitation to join team <strong><a href='/dashboard/team_view/{0}'>'{1}'</a></strong><div></body></html>".format(team.id,team.name)
                    email_message = EmailMultiAlternatives("Team Invitation".format(request.data.get("status")),'',settings.EMAIL_HOST_EMAIL,[participant.user.email],from_email=request.user.email)
                    email_message.attach_alternative(html_message, 'text/html')
                    email_message.send()
                except Exception as e:
                    print(e)
                    pass
            
        return Response({"status":status.HTTP_200_OK,"msg":"Invitation mail send successfuly"},status=status.HTTP_200_OK)
    
    @detail_route(methods=['post'])
    def join_team(self, request, pk=None):
        link = LinkExpiration.objects.filter(url=settings.INVITE_URL.format(pk,request.user.id))
        if not link:
            return Response({"msg":"your link is not valid","status":status.HTTP_403_FORBIDDEN},status=status.HTTP_403_FORBIDDEN)
        link=link[0]
        if link.is_expired:
            return Response({"msg":"your link has been expired",'status':status.HTTP_403_FORBIDDEN},status= status.HTTP_403_FORBIDDEN)
        link.is_expired=True
        link.save()
        
        team = Team.objects.filter(pk=pk)
        if not team:
            return Response({"msg":"Team not found.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        team = team[0]
        invites = Invitation.objects.filter(participants__user=request.user,team=team,status="pending")
        if not invites:
            return Response({"msg":"you are not invited to join a team","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)

        invites = invites[0]    
        
        if len(team.team_members.all()) == self.total_members:
            invites.status = self.request.data.get("status","rejected")
            invites.save()
            return Response({"msg":"Team members joining are completed.","status":status.HTTP_406_NOT_ACCEPTABLE},status=status.HTTP_406_NOT_ACCEPTABLE)

        invites.status = self.request.data.get("status")
        invites.save()
        
        if self.request.data.get("status") == "accepted":
            participant = get_object_or_404(Participant, user=request.user)
            participant.participant_team = team
            participant.save()
            team.partipants.add(participant)
            team.save()
            
        Notification.objects.filter(type="invitation",created_for=request.user).delete()
        return Response({"status":status.HTTP_200_OK,"msg":"You have successfuly {} a team invitation.".format(self.request.data.get("status"))},status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def leave_team(self, request, pk=None):
        team = get_object_or_404(Team, pk=pk)
        if not team:
            return Response({"msg":"Please select a team.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        participant = get_object_or_404(Participant, user=request.user)
        participant.participant_team = None
        participant.save()
        
        team.partipants.remove(participant)
        team.team_request.all().delete()
        team.save()
        
        if len(team.partipants.all()) == self.if_count:
            team.delete()
            return Response({"msg":"'{}' team is deleted because no member left in a team".format(team.name),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        else:
            members = team.partipants.order_by("id")[0]
            team.team_lead = members.user
            team.save()
            
        return Response({"msg":"You leave a team  successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_team_request(self, request, pk=None):
        team = Team.objects.filter(created_by=request.user,pk=pk) 
        if not team:
            return Response({"msg":"You are not a creator of this team.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        team = team[0]
        tr = TeamRequest.objects.filter(team=team,pk=request.data.get("tid"))
        
        if not tr:
           return Response({"msg":"Team request not found.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST) 
        
        tr = tr[0]
        participant = tr.participant
        if participant.participant_team == team:
            return Response(
                {"msg":"Participant {} {} already member of this team '{}'".format(participant.user.first_name,participant.user.last_name,team.name),
                 "status":status.HTTP_409_CONFLICT
                },status=status.HTTP_409_CONFLICT)
            
        if len(team.team_members.all()) == self.total_members:
            return Response({"msg":"Team members joining are completed.","status":status.HTTP_406_NOT_ACCEPTABLE},status=status.HTTP_406_NOT_ACCEPTABLE)
        
        if request.data.get("status") == "approved":
            participant.participant_team = team
            participant.save()
            team.partipants.add(participant)
            team.save()
        data = {
            "title":"Membership {} for team <strong><a href='/dashboard/team_view/{}'>{}</a></strong>".format(request.data.get("status"),team.id,team.name),
            "description":"Your membership {}".format(request.data.get("status")),
            "created_for": participant.user,
            "type":"response",
            "req_data":{}
        }
        Notification.objects.get(id=request.data.get("notification_id")).delete()
        create_notification(data,request)
        
        tr.status = request.data.get("status")
        tr.save()
        tr.delete()
        return Response({"msg":"Team request update successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
  
    @action(methods=["get"],detail=False)
    def myteam(self,request): 
        if request.user.is_anonymous:
            return Response({"msg":"Annonymus user cant access this.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        teams = Team.objects.filter(Q(team_lead = request.user)|Q(created_by = request.user)|Q(team_mentor=request.user))
        if not request.user.is_superuser:
            _teams = Team.objects.filter(partipants__in = Participant.objects.filter(user=request.user))
            teams = teams.union(_teams).order_by('-id')
            
        if request.user.is_judge:
            tmr_teams = [tmr.team for tmr in TeamMentorRequest.objects.filter(for_judge = request.user,judge_status="approved",admin_status="approved").order_by("-team_id")]
            if JudgeRequestTeam.objects.filter(judge__user=request.user,status="approved"):
                for i in JudgeRequestTeam.objects.filter(judge__user=request.user,status="approved"):
                    tmr_teams.append(i.team)
            if Team.objects.filter(team_mentor=request.user):
                for i in Team.objects.filter(team_mentor=request.user):
                    tmr_teams.append(i)
            tmr_teams=list(set(tmr_teams))       
            count=len(tmr_teams)
            tmr_teams = tmr_teams[int(request.query_params.get("offset",0) or 0):int(request.query_params.get("limit",10) or 10)+int(request.query_params.get("offset",0) or 0)]
            resp={
                    "count":count,
                    "status":status.HTTP_200_OK,
                    "data":self.get_serializer(tmr_teams, many=True).data
            }
            return Response(resp,status = status.HTTP_200_OK)
        
        if not teams:
            return Response({"msg":"You hasn't created any team","data":[],"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        queryset = self.filter_queryset(teams)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"status":status.HTTP_200_OK,"data":serializer.data},status = status.HTTP_200_OK) 
            
    @action(methods=["post"],detail=False)    
    def admin_create(self,request):
        if not request.user.is_superuser or not request.user.is_organizer:
            return Response({"msg":"You are not a authorized user to access this","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
            
        data = request.data
        data = {"name":data.get("name"),"logo":data.get('logo',None),"description":data.get("description") if data.get("description") else "" }
            
        team = Team.objects.filter(created_by=request.user,name=data.get("name"))
        if team:
            return Response({"msg":"Team is already exist with same name","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
        
        track = TeamTrack.objects.filter(slug=request.data.get("team_track",None))
        if not track:
            return Response({"msg":"Please select a team track for this team","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        track = track[0]
        
        participants= Participant.objects.filter(id__in=request.data.get("ids").split(","))
        if not participants:
            return Response({"msg":"Please select participants.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        team = Team.objects.create(created_by=request.user,team_track=track,**data) 
        for participant in participants:
            team.partipants.add(participant)
        team.team_lead=participants[0].user
        team.team_track = track
        team.save()
            
        if request.data.get("portfolio",[]):
            portfolio=request.data.pop("portfolio")
            for _docs in portfolio:
                try:
                    TeamPortfolio.objects.get(docs=_docs,team=team)
                except TeamPortfolio.DoesNotExist:
                    TeamPortfolio.objects.create(docs=_docs,team=team)
            
        data={
            "status":status.HTTP_200_OK,
            "data":self.get_serializer(team).data
        }
        return Response(data,status=status.HTTP_200_OK)
    
    @action(methods=["post"],detail=False,url_path="judge-invitation")   
    def send_judge_invitation(self,request,*args,**kwargs):

        if not request.user.is_participant:
            return Response({"msg":"You are not a participant user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        team = Team.objects.filter(id=request.data.get("id"))
        if not team:
            return Response({"msg":"Team not found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        team = team[0]
        
        if TeamMentorRequest.objects.filter(Q(admin_status="pending")|Q(judge_status="pending"),team = team):
            return Response({"msg":"Team request pending for approval. ","status":status.HTTP_300_MULTIPLE_CHOICES},status=status.HTTP_300_MULTIPLE_CHOICES)   

        admin_user=User.objects.filter(is_superuser=True)[0]
        judge = User.objects.get(id=request.data.get("judge_id"),is_judge=True)
        mr=TeamMentorRequest.objects.create(team=team,for_judge=judge,for_admin=admin_user)
        user_list=[admin_user,judge]
        for u in user_list:
            dt={
                "title":"Team mentor request for a judge {} by team <strong><a href='/dashboard/team_view/{}'>{}</a></strong>".format(judge.full_name,team.id,team.name),
                "description":"Team mentor request for a judge {} by team <strong><a href='/dashboard/team_view/{}'>{}</a></strong>".format(judge.full_name,team.id,team.name),
                "created_for": u,
                "type":"mentor-request",
                "req_data":{"mentor_request_id":mr.id}
            }
            create_notification(dt,request)
            
        
        return Response({"msg":"Team request for a team mentor send for admin approval","status":status.HTTP_200_OK},status=status.HTTP_200_OK)   
    
    @action(methods=["post"],detail=True,url_path="team-delete")  
    def admin_delete_team(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to delete team","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        instance = Team.objects.get(id=kwargs.get("pk"))
        self.perform_destroy(instance)
        return Response({"msg":"Team sucessfuly deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(methods=["post"],detail=True,url_path="admin-assing-team-judge")  
    def admin_assing_team_judge(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to delete team","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        user=User.objects.filter(id=request.data.get("judge_id"),is_judge=True,is_active=True)
        if not user:
            return Response({"msg":"Assign user id not found.","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        obj = Team.objects.get(id=kwargs.get("pk"))
        user=user[0]
        if JudgeRequestTeam.objects.filter(team=obj,status__in=["pending","rejected"]):
            JudgeRequestTeam.objects.filter(team=obj,status__in=["pending","rejected"]).delete()
        if TeamMentorRequest.objects.filter(~Q(admin_status = "rejected"),~Q(judge_status = "rejected"),team=obj):
            TeamMentorRequest.objects.filter(~Q(admin_status = "rejected"),~Q(judge_status = "rejected"),team=obj).delete()
        
        
        obj.team_mentor = user
        obj.save()
        
        for participant in obj.partipants.all():
            dt={
                "title":"New judge '{}' assigned by admin to team '{}'".format(user.full_name,obj.name),
                "description":"New judge '{}' assigned by admin to team '{}'".format(user.full_name,obj.name),
                "created_for": participant.user,
                "type":"response",
                "req_data":{}
            }
            create_notification(dt,request)
        
        dt={
            "title":"You have appointed as team mentor of a team {} ".format(obj.name),
            "description":"You have appointed as team mentor of a team {} ".format(obj.name),
            "created_for": user,
            "type":"response",
            "req_data":{}
        }
        create_notification(dt,request)
        if user.assing_as_mentor:
            try:
                html_message="<html><body><h2>You have appointed as team mentor of a team '{}'.</h2><div></body></html>".format(obj.name)
                email_message = EmailMultiAlternatives("Admin assign you as team mentor",'',settings.EMAIL_HOST_EMAIL,[user.email],from_email=request.user.email)
                email_message.attach_alternative(html_message, 'text/html')
                email_message.send()
            except Exception as e:
                print(e)
                pass
        return Response({"msg":"Successfully assign judge to team.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(methods=["post"],detail=True,url_path="admin-remove-team-judge")  
    def admin_remove_team_judge(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not authorized to delete team","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = Team.objects.filter(id=kwargs.get("pk"))
        if not obj:
            return Response({"msg":"Team not found","status":status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        
        obj = obj[0]
        if not obj.team_mentor:
            return Response({"msg":"A team '{}' has no team mentor.".format(obj.name),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
        judge = obj.team_mentor
        
        obj.team_mentor = None
        obj.save()
        
        if JudgeRequestTeam.objects.filter(team=obj,status__in=["pending","rejected"]):
            JudgeRequestTeam.objects.filter(team=obj,status__in=["pending","rejected"]).delete()
        if TeamMentorRequest.objects.filter(~Q(admin_status = "rejected"),~Q(judge_status = "rejected"),team=obj):
            TeamMentorRequest.objects.filter(~Q(admin_status = "rejected"),~Q(judge_status = "rejected"),team=obj).delete()
            
        dt = {
            "title":"You have been removed from a team '{}' as the team's mentor".format(obj.name),
            "description":"Your membership {}".format(request.data.get("status")),
            "created_for": judge,
            "type":"response",
            "req_data":{}
        }
        create_notification(dt,request)
        try:
            for participant in obj.partipants.all():
                dt = {
                    "title":"Your team mentor '{}' is removed by admin  of your team '{}'".format(judge.full_name,obj.name),
                    "description":"Your team mentor '{}' is removed by admin of your team '{}'".format(judge.full_name,obj.name),
                    "created_for": participant.user,
                    "type":"response",
                    "req_data":{}
                }
                create_notification(dt,request)
        except Exception as e:
            print(e)
            pass
            
        return Response({"msg":"Team mentor removed successfully.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
        
class TeamTrackViewsets(viewsets.ModelViewSet):
    """
    track/
    """
    serializer_class = TeamTrackSerializer
    
    def get_queryset(self):
        return TeamTrack.objects.all()
    
    def create(self,request,*args,**kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED) 
        track=self.get_queryset().filter(track_name=request.data.get("track_name")) 
        if track:
            return Response({"msg":"Track already exist with same name","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)    
        super().create(request,*args,**kwargs)
        return Response({"msg":"Track successfully created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Track deleted successfully.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(methods=["post"],detail=True,url_path="edit")  
    def track_update(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"msg":"You are not a authorized user","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        obj = self.get_object()
        if obj.track_name.lower() != request.data.get("track_name").lower():
            if TeamTrack.objects.filter(track_name=request.data.get("track_name")):
                return Response({"status":status.HTTP_409_CONFLICT,"msg": "Track already exist with same name."},status=status.HTTP_409_CONFLICT)
        for key,value in request.data.items():
            setattr(obj,key,value)
        obj.save()
        
        return Response({"msg":"Track updated successfully.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(methods=["get"],detail=True,url_path="team-list")  
    def track_team_list(self, request, *args, **kwargs):
        obj = self.get_object()
        teams = obj.teams.all()
        if request.query_params.get("team_name",None):
            teams = teams.filter(name__icontains=request.query_params.get("team_name"))
            
        task = Task.objects.get(id=request.query_params.get("task_id"))
        judges = [task.judge for task in AssingJudgeToTask.objects.filter(track=obj,task=task)]
        random_team_judges = [task.judge for task in RandomJudgeToTaskAndTeam.objects.filter(task=task)]
        _data = {"judges":UserSerializer(judges,context={"request":request},many=True).data,"teams":[]}
        teams_count = len(teams)
        teams = teams[int(request.query_params.get("offset",0) or 0):int(request.query_params.get("limit",10) or 10)+int(request.query_params.get("offset",0) or 0)]
        
        for team in teams:
            dt = TeamAdminTaskSerializer(team,context={"request":request,"task":task}).data
            dt.update({"random_judges":UserSerializer([task.judge for task in RandomJudgeToTaskAndTeam.objects.filter(task=task,team=team)] ,context={"request":request},many=True).data})
            _data["teams"].append(dt)
            
        lock =  TaskLock.objects.filter(track=obj,task=task)
        if lock:
            lock = lock[0]
            _data.update({"lock_status":lock.lock})
        else:
            _data.update({"lock_status":"false"})
            
        return Response({"data":_data, "count":teams_count,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
class TeamEventViewsets(viewsets.ModelViewSet):
    serializer_class=TeamEventSerializer
    
    def get_queryset(self):
        _date = date.today()
        if self.request.GET.get("team_id",None):
            if self.request.user.is_judge:
                return TeamEvent.objects.filter(team_id=self.request.GET.get("team_id")).annotate(day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
            return TeamEvent.objects.filter(team__partipants__user=self.request.user,team_id=self.request.GET.get("team_id")).annotate(day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
        return TeamEvent.objects.annotate(day_mod=Cast('schedule_date', DateField())).order_by('day_mod')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def create(self,request,*args,**kwargs):
        team = Team.objects.filter((Q(partipants__in = Participant.objects.filter(user=request.user))|Q(team_lead=request.user)|Q(team_mentor=request.user)),
                                   id=request.data.get("team_id"))
        if not team:
            return Response({"msg":"You are not a team member of this team.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        team = team[0]

        participants = Participant.objects.filter(id__in=[participant.get("id") for participant in request.data.pop("participants")])
        inviteJudge = request.data.pop("inviteJudge")
        try:
           team_event = TeamEvent.objects.get(created_by=request.user,team=team,**request.data)
        except TeamEvent.DoesNotExist:
            team_event = TeamEvent.objects.create(created_by=request.user,team=team,**request.data)
        for participant in participants:
            team_event.partipants.add(participant)
            data = {
                "title":"New event {} has been created by {} for team '<strong><a href='/dashboard/team_view/{}'>'{}'</a></strong>".format(
                    team_event.title,request.user.full_name,team.id,team.name),
                "description":"Event Created",
                "type":"response",
                "created_for":participant.user,
                "req_data":{}   
            }
            create_notification(data,request) 
            if participant.user.team_events:
                try:
                    html_message="<html><body><h2>Team events '{}' is created.</h2><div></body></html>".format(team_event.title)
                    email_message = EmailMultiAlternatives("Team events email",'',settings.EMAIL_HOST_EMAIL,[participant.user.email],from_email=request.user.email)
                    email_message.attach_alternative(html_message, 'text/html')
                    email_message.send()
                except Exception as e:
                    print(e)
                    pass
                
        if inviteJudge:
            team_event.team_mentor = team.team_mentor
            data = {
                "title":"New event {} has been created by {} for team '<strong><a href='/dashboard/team_view/{}'>'{}'</a></strong>".format(
                    team_event.title,request.user.full_name,team.id,team.name),
                "description":"Event Created",
                "type":"response",
                "created_for":team.team_mentor,
                "req_data":{}   
            }
            create_notification(data,request) 
        team_event.save()  
        return Response({"msg":"Team Event Sucessfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Team Event sucessfuly deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(detail=True,methods=['post'],url_path="edit")
    def edit_event(self,request,*args,**kwargs):
        event = self.get_object()
        if datetime.strptime(event.schedule_date, '%Y-%m-%d, %H:%M:%S %p') < datetime.now():
            return Response({"msg":"This event can not be edited.","status":status.HTTP_406_NOT_ACCEPTABLE},status=status.HTTP_406_NOT_ACCEPTABLE)
        

        participants = Participant.objects.filter(id__in=[participant.get("id") for participant in request.data.pop("participants")])
        
        for key,value in request.data.items():
            setattr(event,key,value)
            
        event.partipants.clear()
           
        for participant in participants:
            event.partipants.add(participant)
            
        event.save()
        return Response({"msg":"Event Updated sucessfuly","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
class TeamTaskViewsets(viewsets.ModelViewSet):
    serializer_class=TeamTaskSerializer
    
    def get_queryset(self):
        tasks = TeamTask.objects.order_by("-created_on") 
        
        if self.request.GET.get("team_id",None):
            tasks = tasks.filter(team_id=self.request.GET.get("team_id"))
        if self.request.GET.get("mytask",None) == "true":
            tasks = tasks.filter(participants__user=self.request.user)
        return tasks
    
    def get_serializer_context(self):
        return {"request":self.request}
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Team task sucessfuly deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def create(self,request,*args,**kwargs):
        team = Team.objects.filter((Q(partipants__in = Participant.objects.filter(user=request.user))|Q(team_lead=request.user)|Q(team_mentor=request.user)),id=request.data.get("team_id"))
        if not team:
            return Response({"msg":"You are not a team member of this team.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        team = team[0]
        participants = Participant.objects.filter(id__in=[participant.get("id") for participant in request.data.pop("participants")])
        try:
            task = TeamTask.objects.get(created_by=request.user,team=team,**request.data)
        except TeamTask.DoesNotExist:
            task = TeamTask.objects.create(created_by=request.user,team=team,**request.data)
            
        for participant in participants:
            task.participants.add(participant)
            TeamTaskStatus.objects.create(participant=participant,team=team,team_task=task)
            data = {
                "title":"New task {} assigned to you by {} for team '<strong><a href='/dashboard/team_view/{}'>'{}'</a></strong>".format(
                    task.title,request.user.full_name,team.id,team.name),
                "description":"Task Created",
                "type":"response",
                "created_for":participant.user,
                "req_data":{}   
            }
            create_notification(data,request) 
            if participant.user.team_tasks:
                try:
                    html_message="<html><body><h2>Team task '{}' is created.</h2><div></body></html>".format(task.title)
                    email_message = EmailMultiAlternatives("Team task email",'',settings.EMAIL_HOST_EMAIL,[participant.user.email],from_email=request.user.email)
                    email_message.attach_alternative(html_message, 'text/html')
                    email_message.send()
                except Exception as e:
                    print(e)
                    pass
        task.save()    
        return Response({"msg":"Team Task Sucessfuly created.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"data":serializer.data,"status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['post'],url_path="edit")
    def edit_task(self,request,*args,**kwargs):
        task = self.get_object()
      
        participants = Participant.objects.filter(id__in=[participant.get("id") for participant in request.data.pop("participants")])
        
        for key,value in request.data.items():
            setattr(task,key,value)
        task.save()
        
        TeamTaskStatus.objects.filter(participant__in=participants,team=task.team,team_task=task,status="pending").delete()
        task.participants.clear()
        for participant in participants:
            try:
                TeamTaskStatus.objects.get(participant=participant,team=task.team,team_task=task)
            except TeamTaskStatus.DoesNotExist:
                TeamTaskStatus.objects.create(participant=participant,team=task.team,team_task=task)
            task.participants.add(participant) 
            
        task.save()  
        
        return Response({"msg":"Task Updated sucessfuly","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=False,methods=['get'],url_path="todo-list")
    def todo_list(self,request,*args,**kwargs):
        team_tasks = TeamTaskStatus.objects.filter(status="incomplete",participant__user=request.user)
        queryset = self.filter_queryset(team_tasks)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TeamTaskDetailStatusSerializer(page, many=True,context={"request":request})
            return self.get_paginated_response(serializer.data)
 
        serializer = TeamTaskDetailStatusSerializer(queryset, many=True,context={"request":request})
        return Response({"data":serializer.data,"status":status.HTTP_200_OK },status=status.HTTP_200_OK)      
            
class TeamTaskStatusViewsets(viewsets.ModelViewSet):
    serializer_class = TeamTaskStatusSerializer
    
    def get_queryset(self):
        if self.request.user:
            return TeamTaskStatus.objects.filter(participant__user = self.request.user,status="incomplete").order_by("-created_on")
        return TeamTaskStatus.objects.order_by("-created_on")  
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"My task sucessfuly deleted.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['post'],url_path="update")
    def update_task(self,request,*args,**kwargs):
        task = self.get_object()
        task.status=request.data.get("status")
        task.save()                     
        
        return Response({"msg":"Task status updated sucessfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK) 
      
class TeamDocsViewsets(viewsets.ModelViewSet):
    serializer_class=TeamDocsSerializer
    
    filter_backends = (DjangoFilterBackend, )
    filter_class = TeamDocsFilter
    
    def get_queryset(self):
        if self.request.query_params.get("team_id",None):
            return TeamDocs.objects.filter(team_id=self.request.query_params.get("team_id")).order_by("-id")
        return TeamDocs.objects.order_by("-id") 
    
    
    def create(self,request,*args,**kwargs):
        team = Team.objects.filter((Q(partipants = Participant.objects.get(user=request.user))|Q(team_lead=request.user)),id=request.data.get("team_id"))
        if not team:
            return Response({"msg":"You are not a team member of this team.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        team = team[0]
        data=request.data
        doc = TeamDocs.objects.create(created_by=request.user,team=team,doc_name=data.get("doc_name"),doc=request.FILES.get("doc"))
                
        return Response({"msg":"Team docs Sucessfuly uploaded.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"msg":"Doc deletion successfully done .","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
