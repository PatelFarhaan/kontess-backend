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

from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route,action
from django_filters.rest_framework import DjangoFilterBackend


from app.models.team import Team,TeamPortfolio,TeamTrack,Invitation
from app.models.participant import Participant, TeamRequest
from app.serializers.team import TeamSerializer,TeamTrackSerializer
from django.forms.models import model_to_dict
from app.backends.team_filters import TeamFilter

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from app.views.notifications import create_notification
from app.models.notifications import Notification
from django.conf import settings
from django.contrib.auth import get_user_model
from celery.worker.state import total_count
from twilio.rest.api.v2010.account.conference import participant

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
        self.participant = Participant.objects.get(user=self.request.user)
        _teams = Team.objects.filter(partipants = self.participant)
        my_teams = user_teams | _teams
        print(my_teams,teams)
        if self.request.query_params.get("track",None):
            track = TeamTrack.objects.get(slug=self.request.query_params.get("track"))
            return teams.filter(team_track=track).difference(my_teams) 
        return teams.difference(my_teams) 
    
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def get_data(self):
        return {'created_by': self.request.user}

    def create(self, request, *args, **kwargs):
        data = request.data
        data = {"name":data.get("name"),"logo":data.get('logo',None),"description":data.get("description") if data.get("description") else "" }
        team = Team.objects.filter(created_by=request.user,name=data.get("name"))
        if team:
            return Response({"msg":"Team is already exist with same name","status":status.HTTP_409_CONFLICT},status=status.HTTP_409_CONFLICT)
        
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
        team = get_object_or_404(self.get_queryset(), pk=pk)
        
        data = request.data
        data = {"name":data.get("name"),"description":data.get("description") if data.get("description") else "" }
        if request.data.get('logo',None):
            data.update({"logo":request.data.get('logo',None)})
            
        if team.name.lower() != data.get("name").lower():
            if Team.objects.filter(name=data.get("name"),description=data.get("description")):
                data={
                        "status":status.HTTP_409_CONFLICT,
                        "msg": "Team is already exist with same name and description."
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
        
        team = get_object_or_404(self.get_queryset(), pk=pk)
        users = User.objects.filter(id__in=[participant.get("id") for participant in participants])
        participants = Participant.objects.filter(user__in=users)
        team_owner = team.created_by.email
        mail_subject = "Invitations to join team '{}'".format(team.name)
        for participant in participants:
            msg="Dear {},\n You have been invited to join team {}. To join,Please click on the link {}".format(
                participant.user.full_name,team.name,settings.INVITE_URL.format(team.id)
            )
            invitation = Invitation.objects.create(participants=participant,team=team,status="pending",created_by=request.user)
            
            email = EmailMultiAlternatives(mail_subject, body=msg, to=[participant.user.email], from_email=team_owner)
            email.send()
            
            invitation.email_send = True
            invitation.save()
            
        return Response({"status":status.HTTP_200_OK,"msg":"Invitation mail send successfuly"},status=status.HTTP_200_OK)
    
    @detail_route(methods=['post'])
    def join_team(self, request, pk=None):
        
        team = self.get_queryset().filter(pk=pk)
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
        
        return Response({"status":status.HTTP_200_OK,"msg":"You have successfuly {} a team invitation.".format(self.request.data.get("status"))},status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def leave_team(self, request, pk=None):
        team = get_object_or_404(self.get_queryset(), pk=pk)
        if not team:
            return Response({"msg":"Please select a team.","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        participant = get_object_or_404(Participant, user=request.user)
        participant.participant_team = None
        participant.save()
        team.partipants.remove(participant)
        team.team_request.all().delete()
        team.save()
        
        if len(team.team_members.all()) == self.if_team_member:
            team.delete()
            return Response({"msg":"'{}' team is deleted because no member left in a team".format(team.name),"status":status.HTTP_200_OK},status=status.HTTP_200_OK)

        return Response({"msg":"You team leave successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)

    @action(methods=["post"],detail=True)
    def update_team_request(self, request, pk=None):
        team = self.get_queryset().filter(created_by=request.user,pk=pk)
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
            "title":"Membership {} for team <strong>{}</strong>.".format(request.data.get("status"),team.name),
            "description":"Your membership {}".format(request.data.get("status")),
            "created_for": participant.user,
            "type":"response",
            "req_data":{}
        }
        Notification.objects.get(id=request.data.get("notification_id")).delete()
        create_notification(data,request)
        
        tr.status = request.data.get("status")
        tr.save()
        
        return Response({"msg":"Team request update successfuly.","status":status.HTTP_200_OK},status=status.HTTP_200_OK)
    
    @action(methods=["get"],detail=False)
    def myteam(self,request): 
        if request.user.is_anonymous:
            return Response({"msg":"Annonymus user cant access this.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        teams = Team.objects.filter(Q(team_lead = request.user)|Q(created_by = request.user))
        _teams = Team.objects.filter(partipants = self.participant)
        
        teams = teams.union(_teams)
        
        if not teams:
            return Response({"msg":"You hasn't created any team","status":status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.filter_queryset(teams)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"status":status.HTTP_200_OK,"data":myteams},status=status.HTTP_200_OK) 
            
    @action(methods=["get"],detail=False)    
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


class TeamTrackViewsets(viewsets.ModelViewSet):
    """
    track/
    """
    serializer_class = TeamTrackSerializer
    
    def get_queryset(self):
        return TeamTrack.objects.all()
    
    