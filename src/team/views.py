# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
import jwt

from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.decorators import login_required

from .models import Team
from .serializers import TeamSerializer
from participant.serializers import ParticipantSerializer

# Create your views here.
def authloginfindwheretoputthiswithgoodinternet():
    if "Authentication" not in request.headers:
        return Response(
            data={
                "message":"not authorized"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    token = jwt.decode(request.headers["Authentication"],None,None)
    if(token["id"] != request.user.id):
        return Response(
            data={
                "message":"not authorized"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

@login_required
class TeamViewSet(viewsets.ModelViewSet):
    """
    team/
    """
    serializer_class = TeamSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Team.objects.all()
    authentication_classes = (TokenAuthentication,)

    def create(self, request, *args, **kwargs):
        name = request.data.get("name", "")
        description = request.data.get("description")
        user = request.data.user
        participant = Participant.objects.get(user=user)

        if not name or not description or not user or not participant:
            return Response(
                data={
                    "message": "you're missing info"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if(participant.team): 
            return Response(
                data={
                    "message": "user is already in a team"
                }
                status=status.HTTP_400_BAD_REQUEST
            )

        team = Team.objects.create(name=name, description=description)
        team.save()
        participant.team = team
        participant.save()

        return Response(
            data=TeamSerializer(team).data,
            status=status.HTTP_201_CREATED
        )

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