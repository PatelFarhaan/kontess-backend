# Create your views here.
from app.models.user import User
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import detail_route, list_route
from app.serializers.user import UserSerializer

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

