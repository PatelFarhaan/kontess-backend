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
from rest_framework.validators import UniqueValidator

import json
from app.models.participant import Participant, TeamRequest
from app.serializers.user import UserSerializer


class ParticipantDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Participant
        fields = ('id', 'user')
    
    def get_user(self, obj):
         
        return UserSerializer(obj.user,context={"request":self.context.get("request")}).data



class TeamRequestSerializer(serializers.ModelSerializer):
    participant = ParticipantDetailSerializer(required=False,allow_null=True)
    class Meta:
        model = TeamRequest
        fields = ('id', 'essay','team','participant','status')
        read_only_fields=("team","status","participant")


class TeamRequestDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRequest
        fields = ('id', 'status')
        