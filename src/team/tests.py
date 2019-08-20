from django.test import TestCase
from .models import Team

# Create your tests here.
class TeamTest(TestCase):
    def create_team(self, name="only a test", description="yes, this is only a test"):
        return Team.objects.create(name=name, description=description)

    def test_team_create(self):
        t = self.create_team()
        self.assertTrue(isinstance(t, Team))
        self.assertEqual(t.__unicode__(), t.name)