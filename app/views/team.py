# Create your views here.
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route

from app.models.team import Team
from app.models.participant import Participant, TeamRequest
from app.serializers.team import TeamSerializer


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
    queryset = Team.objects.all()

    def get_data(self):
        return {'created_by': self.request.user}

    def create(self, request, *args, **kwargs):
        # serializer = TeamSerializer(data=request.data, context={'request': request})
        if not (request.user.is_organizer or request.user.is_superuser):
            return Response("you dont have permission to create team", status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        serializer = TeamSerializer(team)
        return Response(serializer.data)
    
    @detail_route(methods=['put'])
    def join_team(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        participant = get_object_or_404(Participant.objects.all(), pk=request.data["userId"])
        participant.team = team
        participant.save()
        return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['patch'])
    def leave_team(self, request, pk=None):
        team = get_object_or_404(self.queryset, pk=pk)
        participant = get_object_or_404(Participant.objects.all(), pk=request.data["userId"])
        participant.team = None
        participant.save()
        return Response(status=status.HTTP_200_OK)

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
