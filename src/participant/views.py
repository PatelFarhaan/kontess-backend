from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, action
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

from .models import Participant
from .serializers import UserSerializer, ParticipantSerializer

# Create your views here.
class ParticipantView(viewsets.ModelViewSet):
    serializer_class = ParticipantSerializer
    permission_classes = (permissions.AllowAny,)
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
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        serializer = ParticipantSerializer(self.queryset, many=True)
        return Response(serializer.data)
    
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

                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    @detail_route
    def teamrequest(self, request, pk=None):
        # do this
        pass
    
    @detail_route
    def jointeam(self, request, pk=None):
        # do this
        pass
