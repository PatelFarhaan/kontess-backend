from django.http import HttpResponse
from rest_framework import status
import json

class RequestHandler(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        url_path = ["login","signup","token","join_team","activate","forgotpasswordemail","reset_password"]
        paths = request.path.split('/')
       
#         if request.user.is_anonymous:
#             if list(set(url_path) & set(paths)):
#                 response = self.get_response(request)
#                 return response
#             else:
#                 return HttpResponse(
#                     json.dumps({"msg":"You can access api without login","status":status.HTTP_401_UNAUTHORIZED}),
#                         content_type='application/json',
#                         status=status.HTTP_401_UNAUTHORIZED
#                 )
            
            
        response = self.get_response(request)
        return response