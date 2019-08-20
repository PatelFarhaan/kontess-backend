from django.test import TestCase
from django.contrib.auth.models import User
from .models import Participant, TeamRequest
from team.models import Team

# Create your tests here.
class ParticipantTest(TestCase):
    def create_participant(self, f="test", l="test", u="email", p="testtest", graduation_year=2022):
        u = User.objects.create(
            first_name=f, 
            last_name=l,
            username=u,
            password=p)
        return Participant.objects.create(user=u, graduation_year=graduation_year)

    def test_participant_create(self):
        p = self.create_participant()
        self.assertTrue(isinstance(p, Participant))
        failed = False
        try:
            p = self.create_participant(graduation_year="fail")
        except:
            failed = True
        self.assertTrue(failed)

class TeamRequestTest(TestCase):
    def create_participant(self):
        u = User.objects.create(
            first_name="test", 
            last_name="test",
            username="test",
            password="test")
        return Participant.objects.create(user=u, graduation_year=2022)

    def create_team(self):
        return Team.objects.create(name="test", description="test")

    def create_tr(self, p, t, essay):
        return TeamRequest.objects.create(participant=p, team=t, essay=essay)

    def test_participant_create(self):
        tr = self.create_tr(self.create_participant(), self.create_team(), "essay")
        self.assertTrue(isinstance(tr, TeamRequest))