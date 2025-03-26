import os
from django.shortcuts import get_object_or_404
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction


from .models import WaletUser
from .serializers import RegisterUserSerializer, CustomTokenObtainPairSerializer



class RegisterUser(APIView):
    def post(self, request):
        ''' Expected { username, password, email } key in req body'''
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            notification_url = os.getenv("NOTIFICATION_URL", "http://localhost:8001") + "/email/verify-user"
            email_payload = {
                "to": user.email,
                "context": {
                    "username": user.username,
                    "verification_link": f"http://localhost:8000/api/auth/verify/{user.username}" #TODO: change to fe link for verifying user
                }
            }

            response = requests.post(notification_url, json=email_payload)
            if response.status_code != 200:
                return Response(
                    {"error": "Failed to send notification", "details": response.json()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyUser(APIView):
    def post(self, request, username):
        user = get_object_or_404(WaletUser, username=username)
        if user.is_active:
            return Response({"detail": "user already activated"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            user.is_active = True
            user.save()
            return Response({"detail": "succesfully activate user"}, status=status.HTTP_200_OK)

class LoginUser(APIView):
    def post(self, request):
        ''' Expecting { username, password } key in req body'''
        data = {
            "username": request.data.get('username'),
            "password": request.data.get('password')
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)