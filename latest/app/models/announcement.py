
# Create your models here.
from django.db import models
from app.models.user import User

# Create your models here.
class Announcement(models.Model):
    #title= models.CharField(max_length=50)
    description = models.TextField(null=True,blank=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="announcements")
    created_on = models.DateTimeField(auto_now_add=True)
    announcement_type = models.CharField(choices=(("every_one","To Every One"),("participants","Participants Only"),("judges","Judges")),max_length=50)

    class Meta:
        ordering=['-id','-created_on']

    def __str__(self):
        return "{}".format(self.title)

class AnnouncementStatus(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="announcement_status")
    announcement = models.ForeignKey(Announcement,on_delete=models.CASCADE,related_name="status")
    is_star = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)
