from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, action


from .models import Organizer
from .serializers import OrganizerSerializer
from participant.serializers import UserSerializer

# Create your views here.
class OrganizerViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizerSerializer
    permission_classes_by_action = {'create': [permissions.AllowAny],
                                    'login': [permissions.AllowAny],
                                    'retrieve': [permissions.AllowAny],
                                    'list': [permissions.IsAuthenticated]}
    queryset = Organizer.objects.all()

    def create(self, request):
        title = request.data.pop('title')
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if(not title):
                return HttpResponseBadRequest(
                    'missing information'
                )
            o = Organizer.objects.create(
                user=user,
                title=title
            )
            o.save()
            return Response(OrganizerSerializer(o).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        serializer = OrganizerSerializer(self.queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        organizer = get_object_or_404(self.queryset, pk=pk)
        serializer = OrganizerSerializer(organizer)
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
    