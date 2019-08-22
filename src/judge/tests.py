from django.test import TestCase
from django.contrib.auth.models import User
from .models import Judge

# Create your tests here.
class JudgeTest(TestCase):
    def create_judge(self, f="test", l="test", u="email", p="testtest", title="reee"):
        u = User.objects.create(
            first_name=f, 
            last_name=l,
            username=u,
            password=p)
        return Judge.objects.create(user=u, title=title)

    def test_participant_create(self):
        j = self.create_judge()
        self.assertTrue(isinstance(j, Judge))
        failed = False
        try:
            p = self.create_judge(title=20)
        except:
            failed = True
        self.assertTrue(failed)