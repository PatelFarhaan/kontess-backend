from django.test import TestCase
from django.contrib.auth.models import User
from .models import Organizer

# Create your tests here.
class OrganizertTest(TestCase):
    def create_organizer(self, f="test", l="test", u="email", p="testtest", title="reee"):
        u = User.objects.create(
            first_name=f, 
            last_name=l,
            username=u,
            password=p)
        return Organizer.objects.create(user=u, title=title)

    def test_participant_create(self):
        o = self.create_organizer()
        self.assertTrue(isinstance(o, Organizer))
        failed = False
        try:
            p = self.create_participant(title=20)
        except:
            failed = True
        self.assertTrue(failed)