from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, action

from .models import Participant, TeamRequest
from team.models import Team
from .serializers import UserSerializer, ParticipantSerializer, TeamRequestSerializer

# Create your views here.
class ParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = ParticipantSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'create_team_request': [permissions.IsAuthenticated]}
    queryset = Participant.objects.all()

    def create(self, request):
        graduation_year = request.data.pop('graduation_year')
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if(not graduation_year):
                return HttpResponseBadRequest(
                    'missing information'
                )
            p = Participant.objects.create(
                user=user,
                graduation_year=graduation_year
            )
            p.save()
            return Response(ParticipantSerializer(p).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        # serializer = ParticipantSerializer(self.queryset, many=True)
        page = self.paginate_queryset(self.queryset)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data.data)
    
    def retrieve(self, request, pk=None):
        participant = get_object_or_404(self.queryset, pk=pk)
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)

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
                    ParticipantSerializer(participant).data, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    @detail_route(methods=['post'])
    def create_team_request(self, request, pk=None):
        p = get_object_or_404(self.queryset, pk=pk)
        t = get_object_or_404(Team.objects.all(), pk=request.data["teamId"])
        if(TeamRequest.objects.filter(participant=p).filter(team=t).count() != 0):
            return Response("already requested", status=status.HTTP_409_CONFLICT)
        essay = request.data["essay"]
        tr = TeamRequest.objects.create(participant=p, team=t, essay=essay)
        return Response(TeamRequestSerializer(tr).data, status=status.HTTP_201_CREATED)