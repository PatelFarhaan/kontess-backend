# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.decorators import login_required

from .models import Team
from participant.models import Participant
from .serializers import TeamSerializer
from participant.serializers import ParticipantSerializer


class TeamViewSet(viewsets.ModelViewSet):
    """
    team/
    """
    serializer_class = TeamSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Team.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            team = serializer.save()
            user = User.objects.get(id=request.user.id)
            participant = Participant.objects.get(user=user)
            participant.team = team
            participant.save()
            return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        serializer = TeamSerializer(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        group = get_object_or_404(self.queryset, pk=pk)
        serializer = TeamSerializer(group)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def get_team_members(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        participants = Participant.objects.filter(team=team)
        return ParticipantSerializer(participants, many=True).data