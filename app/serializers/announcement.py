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


from rest_framework import serializers

from app.models.announcement import Announcement,AnnouncementStatus
from app.serializers.user import UserSerializer



class AnnouncementSerializer(serializers.ModelSerializer):
    created_by=UserSerializer(required=False,allow_null=True)
    class Meta:
        model = Announcement
        fields = "__all__"


class AnnouncementStatusSerializer(serializers.ModelSerializer):
    announcement= AnnouncementSerializer(required=False,allow_null=True)
    user = UserSerializer(required=False,allow_null=True)
    class Meta:
        model = AnnouncementStatus
        fields = "__all__"
    
    