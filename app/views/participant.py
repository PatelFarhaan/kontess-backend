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

from django.contrib.auth import authenticate, login, logout,get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, action

from app.models.participant import Participant, TeamRequest
from app.models.team import Team
from app.models.judge import JudgeRequestTeam,Judge
from app.serializers.user import UserSerializer
from app.serializers.participant import ParticipantDetailSerializer,TeamRequestSerializer
from app.views.notifications import create_notification 
from app.models.notifications import Notification

User = get_user_model()

# Create your views here.
class ParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipantDetailSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'create_team_request': [permissions.IsAuthenticated]}
    queryset = Participant.objects.all()
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    
    def create(self, request):
        title = request.data.pop('title')
        serializer = UserSerializer(data=request.data,context={"request":self.request})
        if serializer.is_valid():
            user = serializer.save()
            if(not title):
                return HttpResponseBadRequest(
                    'missing information'
                )
            p = Participant.objects.create(
                user=user,
                title=title
            )
            p.save()
            return Response(ParticipantDetailSerializer(p).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        participant = get_object_or_404(self.queryset, pk=pk)
        serializer = ParticipantDetailSerializer(participant)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                participant = get_object_or_404(self.queryset, user=user)
                return Response(
                    ParticipantDetailSerializer(participant).data, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def create_team_request(self, request):
        if request.user.is_anonymous:
            return Response({"msg":"Annonymus user cant access this.","status":status.HTTP_401_UNAUTHORIZED},status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.is_judge:
            team = Team.objects.get(id=self.request.data.get("teamId"))
            judge = Judge.objects.get(user=request.user)
            if not JudgeRequestTeam.objects.filter(judge=judge,team=team):
                jrt = JudgeRequestTeam.objects.create(judge=judge,team=team,status="pending",created_for=User.objects.filter(is_superuser=True)[0])
                
                data={
                    "title":"{} joining request for team {} as judge".format(request.user.full_name,team.name),
                    "description":"Joining request for team as judge",
                    "req_data":{
                        "team_id":team.id,
                        "judge_team_request_id":jrt.id
                    },
                    "type":"judge-request-team"
                }
                notification = Notification.objects.create(created_by=request.user,created_for=User.objects.filter(is_superuser=True)[0],**data)
    
                return Response({"msg":"{} joining request for team {} as judge sucessfully send to admin.".format(request.user.full_name,team.name),"status":status.HTTP_200_OK}, status=status.HTTP_200_OK)
            return Response({"msg":"Already requested for this team.","status":status.HTTP_403_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
        
        p = get_object_or_404(self.queryset,user = request.user)
        t = get_object_or_404(Team.objects.all(), pk = request.data.get("teamId"))
        if(TeamRequest.objects.filter(participant=p).filter(team=t).count() != 0):
            data={"msg":"already requested", "status":status.HTTP_409_CONFLICT}
            return Response(data)
        
        essay = request.data.get("essay")
        tr = TeamRequest.objects.create(participant=p, team=t, essay=essay, status = 'pending')
        if tr:
            data={
                "title":"<strong><a href='/dashboard/profile/{0}'>{1}</a></strong> sent you a request to join team <strong><a href='/dashboard/team_view/{2}'>{3}</a></strong>.".format(
                    p.user.id,p.user.full_name,tr.team.id,tr.team.name),
                "description":"Joining request for team",
                "created_for":tr.team.created_by,
                "req_data":{
                    "team_id":tr.team.id,
                    "team_request_id":tr.id
                },
                "type":"request"
            }
            create_notification(data,request)
        data={
            "status":status.HTTP_200_OK,
            "data":TeamRequestSerializer(tr,context=self.get_serializer_context()).data,
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
