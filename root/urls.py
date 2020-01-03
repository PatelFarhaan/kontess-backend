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
from app.views.team import TeamViewSet,TeamTrackViewsets,TeamEventViewsets,TeamTaskViewsets,TeamDocsViewsets,TeamTaskStatusViewsets
from app.views.organizer import OrganizerViewSet
from app.views.judge import JudgeViewSet,JudgeRequestViewsets,TeamMentorRequestViewsets,JudgeRequestTeamViewsets
from app.views.user import UserViewSet,TokenView,UserSkillViewsets,ManageRegistrationViewsets
from app.views.announcement import AnnouncementViewsets,AnnouncementStatusViewsets
from app.views.notifications import NotificationViewsets
from app.views.events import EventsViewsets,EventLogViewsets,EventView
from app.views.task import TaskViewsets,ParticipantTaskViewset,TaskGradingViewset

from rest_framework_swagger.views import get_swagger_view

router = routers.DefaultRouter()
router.register(r'participant', ParticipantViewSet, base_name='participant')
router.register(r'team', TeamViewSet, base_name='team')
router.register(r'track', TeamTrackViewsets, base_name='track')

router.register(r'organizer', OrganizerViewSet, base_name='organizer')
router.register(r'judge', JudgeViewSet, base_name='judge')
router.register(r'judge-request', JudgeRequestViewsets, base_name='judge_request')
router.register(r'jrt', JudgeRequestTeamViewsets, base_name='judge_request_team')

router.register(r'user', UserViewSet, base_name='user')
router.register(r'announcement', AnnouncementViewsets, base_name='annoucement')
router.register(r'announcement_status', AnnouncementStatusViewsets, base_name='announcement_status')
router.register(r'notification', NotificationViewsets, base_name='notification')
router.register(r'event', EventsViewsets, base_name='event')
router.register(r'event_logs', EventLogViewsets, base_name='event_logs')
router.register(r'team_event', TeamEventViewsets, base_name='team_event')
router.register(r'team_task', TeamTaskViewsets, base_name='team_task')
router.register(r'team_docs', TeamDocsViewsets, base_name='team_docs')
router.register(r'task_status', TeamTaskStatusViewsets, base_name='task_status')
router.register(r'mentor-request', TeamMentorRequestViewsets, base_name='mentor_status')
router.register(r'task', TaskViewsets, base_name='admin_task')
router.register(r'participant_task', ParticipantTaskViewset, base_name='participant_task')
router.register(r'grading', TaskGradingViewset, base_name='judge_task')

router.register(r'user_skill', UserSkillViewsets, base_name='skill')
router.register(r'manage-registration', ManageRegistrationViewsets, base_name='manage_registration')

schema_view = get_swagger_view(title='Kontess API')

urlpatterns = [
    # Your URLs...Z
    path('admin/', admin.site.urls),
    path('api/token/', TokenView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path(r'api/', include(router.urls)),
    path('swagger-ui/', schema_view),
    path("api/my-event/",EventView.as_view(),name="my-event"),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
