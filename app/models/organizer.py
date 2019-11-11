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

from django.db import models
from app.models.user import User

# Create your models here.
class Organizer(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name=("auth_user"),
        on_delete=models.CASCADE
    )

    def __unicode__(self):
        return "{0} {1}".format(self.user.first_name, self.user.last_name)
