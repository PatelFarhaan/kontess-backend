'''
/**
 *@copyright : ToXSL Technologies Pvt. Ltd. < www.toxsl.com >
 *@author     : Shiv Charan Panjeta < shiv@toxsl.com >
 *
 * All Rights Reserved.
 * Proprietary and confidential :  All information contained herein is, and remains
 * the property of ToXSL Technologies Pvt. Ltd. and its partners.
 * Unauthorized copying of this file, via any medium is strictly prohibited.
 *
 *
 */
'''

from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views
from django.views.generic import TemplateView

from app.views.participant import ParticipantViewSet
from app.views.team import TeamViewSet,TeamTrackViewsets
from app.views.organizer import OrganizerViewSet
from app.views.judge import JudgeViewSet
from app.views.user import UserViewSet,TokenView
from app.views.announcement import AnnouncementViewsets,AnnouncementStatusViewsets
from app.views.notifications import NotificationViewsets

from rest_framework_swagger.views import get_swagger_view

router = routers.DefaultRouter()
router.register(r'participant', ParticipantViewSet, base_name='participant')
router.register(r'team', TeamViewSet, base_name='team')
router.register(r'track', TeamTrackViewsets, base_name='track')

router.register(r'organizer', OrganizerViewSet, base_name='organizer')
router.register(r'judge', JudgeViewSet, base_name='judge')
router.register(r'user', UserViewSet, base_name='user')
router.register(r'announcement', AnnouncementViewsets, base_name='annoucement')
router.register(r'announcement_status', AnnouncementStatusViewsets, base_name='announcement_status')
router.register(r'notification', NotificationViewsets, base_name='notification')

schema_view = get_swagger_view(title='Kontess API')

urlpatterns = [
    # Your URLs...Z
    path('admin/', admin.site.urls),
    path('api/token/', TokenView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
    path('swagger-ui/', schema_view),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
