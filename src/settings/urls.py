"""src URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views
from django.views.generic import TemplateView

from participant.views import ParticipantViewSet
from team.views import TeamViewSet
from organizer.views import OrganizerViewSet
from judge.views import JudgeViewSet
from rest_framework_swagger.views import get_swagger_view

router = routers.DefaultRouter()
router.register(r'participant', ParticipantViewSet, base_name='participant')
router.register(r'team', TeamViewSet, base_name='team')
router.register(r'organizer', OrganizerViewSet, base_name='organizer')
router.register(r'judge', JudgeViewSet, base_name='judge')

schema_view = get_swagger_view(title='Kontess API')

urlpatterns = [
    # Your URLs...Z
    path('admin/', admin.site.urls),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
    path('swagger-ui/', schema_view),
]
