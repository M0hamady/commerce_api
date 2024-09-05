import json
from django.contrib.auth import logout
# Create your views here.
from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed

from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from api.token_blacklist import add_to_blacklist, is_token_revoked
from store.views import get_user_from_token
from .models import   User
from .serializers import   UserImageSerializer, UserSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.utils import jwt_decode_handler
from django.contrib.auth import authenticate, login
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_jwt.utils import jwt_encode_handler, jwt_decode_handler
from datetime import datetime
from django.conf import settings


def jwt_payload_handler(user):
    return {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    }

class CustomLoginView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')
            password = data.get('password')
            print('trying to login : ', username, 'and pass ',password)
            # Process the data as needed
        except:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            token = jwt_encode_handler(jwt_payload_handler(user))
            print(f"'positionTitle':{user.job_position_title} , 'PoditionDescription':{user.position_title}")
            return JsonResponse({'message': 'Login successful', 'token': token, 'username': username, 'positionTitle':user.job_position_title , 'PoditionDescription':user.position_title}, status=200)
        else:
            print('failed')
            return JsonResponse({'message': 'Invalid username or password'}, status=401)


class UserRegistrationView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        # Check if the content type is JSON
        if 'application/json' in request.content_type:
            # Parse JSON data from request body
            data = json.loads(request.body)
        else:
            # Assume form-encoded data
            data = request.POST
        
        serializer = UserRegistrationSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        else:
            errors = serializer.errors
            return JsonResponse(errors, status=400)

class CustomObtainTokenView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[1]
        
        if not token:
            return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

        decoded_token = jwt_decode_handler(token)
        user_id = decoded_token.get('user_id')

        if not user_id:
            return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

        return Response({'token': token, 'username': user.username})
    
    
class LogoutView(APIView):
    def post(self, request):
        token = request.data.get('token')  # Get the token from the request body

        if token:
            if is_token_revoked(token):  # Check if the token is already revoked
                return Response({'detail': 'Token already revoked'}, status=400)

            add_to_blacklist(token)  # Add the token to the blacklist or mark it as revoked
            logout(request)
            return Response({'detail': 'Logout successful'})
        else:
            return Response({'detail': 'Token not provided'}, status=400)


class RefreshTokenView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[1]

        if not token:
            return Response({"authenticated": False, "message": "Token not provided"}, status=status.HTTP_404_NOT_FOUND)

        decoded_token = jwt_decode_handler(token)
        user_id = decoded_token.get('user_id')

        if not user_id:
            return Response({"authenticated": False, "message": "Invalid token"}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"authenticated": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate a new token
        new_token = jwt_encode_handler(jwt_payload_handler(user))
        
        return Response({'token': new_token, 'username': user.username})


class VerifyTokenView(APIView):
    def post(self, request):
        

        token = request.data.get('token')  # Get the token from the request body

        if not token:
            return Response({'authenticated': False, 'message': 'Token not provided'}, status=status.HTTP_400_BAD_REQUEST)  # Get the token from the request body

        if token and is_token_revoked(token):  # Check if the token is in the blacklist
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({'authenticated': True})

class UserFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        return self.handle_request(request, 'POST')

    def get(self, request, format=None):
        return self.handle_request(request, 'GET')

    def put(self, request, format=None):
        return self.handle_request(request, 'PUT')

    def delete(self, request, format=None):
        return self.handle_request(request, 'DELETE')

    def handle_request(self, request, method):
        try:
            self.authenticate(request)
        except AuthenticationFailed as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserImageSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            image = request.FILES.get('image')

            if method == 'POST':
                user.image = image
                
            elif method == 'PUT':
                if user.image:
                    user.image.delete()  # Delete the existing image
                user.image = image
            elif method == 'DELETE':
                if user.image:
                    user.image.delete()
                    user.image = None

            user.save()

            context = {
                'user': user.username,
                'image': user.get_image_url
            }
            return Response(context)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]  # Get the token from the Authorization header

        try:
            payload = jwt_decode_handler(token)
            decoded_token = jwt_decode_handler(token)
            user_id = decoded_token['user_id']
            user = User.objects.get(pk=user_id)
            request.user = user
        except Exception as e:
            raise AuthenticationFailed('Invalid token.')

class UserViewSet(viewsets.ViewSet):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        try:
            # Extract token from the request headers
            token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
            user = get_user_from_token(token)  # Decode and verify the token
            request.user = user
        except Exception as e:
            print('Token error:', e)
            # Raise an authentication failed exception if there is an issue
            raise AuthenticationFailed('Invalid token.')

    def retrieve(self, request, pk=None):
        print(111)
        # Retrieve user data
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
