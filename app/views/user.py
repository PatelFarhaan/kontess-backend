# Create your views here.
from app.models.user import User
from app.models.judge import Judge
from app.models.organizer import Organizer
from app.models.participant import Participant

from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route, action
from app.serializers.user import UserSerializer, LoginSerializer
from app.serializers.judge import JudgeSerializer
from app.serializers.organizer import OrganizerSerializer
from app.serializers.participant import ParticipantSerializer

from django.contrib.auth import authenticate, login

class UserViewSet(viewsets.ModelViewSet):
    """
    user/
    """
    serializer_class = UserSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated],
                                    'create_team_request': [permissions.IsAuthenticated]}
    queryset = User.objects.all()


    @action(detail=False, methods=['post'])
    def signup(self, request):

        role = request.data.get('role', None)

        if role not in ["judge", "organizer", "participant"]:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if role == "judge":
            user.is_judge = True
            judge = Judge.objects.create(user=user)
            judge.save()
            user.save()
            return Response(JudgeSerializer(judge).data, status=status.HTTP_201_CREATED)

        elif role == "organizer":
            user.is_organizer = True
            organizer = Organizer.objects.create(user=user)
            organizer.save()
            user.save()
            return Response(OrganizerSerializer(organizer).data, status=status.HTTP_201_CREATED)

        elif role == "participant":
            user.is_participant = True
            participant = Participant.objects.create(user=user)
            participant.save()
            return Response(ParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def login(self, request):

        username = request.data.get('username', None)
        password = request.data.get('password', None)

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return Response(
                    UserSerializer(user).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def get_serializer_class(self):
        if self.action == 'login':
            return LoginSerializer

        return UserSerializer
