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

from app.models.organizer import Organizer
from app.serializers.user import UserSerializer

class OrganizerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Organizer
        fields = ('id', 'user')

    def get_user(self, obj):
        return UserSerializer(obj.user,context={"request":self.context.get("request")}).data