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

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    full_name = models.CharField(max_length=100, default="")
    user_image = models.FileField(upload_to="profile",null=True,blank=True)
    biography = models.TextField(null=True,blank=True)
    
    is_judge = models.BooleanField('judge status', default=False)
    is_participant = models.BooleanField('participant status', default=False)
    is_organizer = models.BooleanField('organizer status', default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    @property
    def role(self):
        if self.is_judge:
            return "judge"

        elif self.is_participant:
            return "participant"

        elif self.is_organizer:

            return "organizer"
        
        elif self.is_superuser:
            return "admin";