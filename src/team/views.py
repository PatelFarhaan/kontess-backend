# Create your views here.
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route

from .models import Team
from participant.models import Participant, TeamRequest
from .serializers import TeamSerializer

class TeamViewSet(viewsets.ModelViewSet):
    """
    team/
    """
    serializer_class = TeamSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'accept_team_request': [permissions.IsAuthenticated],
                                    'reject_team_request': [permissions.IsAuthenticated]}
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
        team = get_object_or_404(self.queryset, pk=pk)
        serializer = TeamSerializer(team)
        return Response(serializer.data)
    
    @detail_route(methods=['post'])
    def accept_team_request(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        request = get_object_or_404(TeamRequest.objects.all(), pk=request.data["requestId"])
        p = request.participant
        if p.team:
            return Response("participant in another team",status=status.HTTP_200_OK)
        p.team = team
        p.save()
        request.delete()
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['delete'])
    def reject_team_request(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        request = get_object_or_404(TeamRequest.objects.all(), pk=request.data["requestId"])
        if(request.team == team):
            request.delete()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)