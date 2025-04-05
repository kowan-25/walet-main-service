import os
from django.shortcuts import get_object_or_404
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import VerifyToken, WaletUser
from .serializers import RegisterUserSerializer, CustomTokenObtainPairSerializer


class RegisterUser(APIView):
    def post(self, request):
        ''' Expected { username, password, email } key in req body'''
        with transaction.atomic():
            serializer = RegisterUserSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    user = serializer.save()
                    verifyToken = VerifyToken.objects.create(
                        user_id=user.id
                    )
                    verifyToken.save()

                    notification_url = os.getenv("NOTIFICATION_URL", "http://localhost:8001") + "/email/verify-user"

                    email_payload = {
                        "to": user.email,
                        "context": {
                            "username": user.username,
                            "verification_link": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify/{verifyToken.id}",
                        }
                    }

                    response = requests.post(notification_url, json=email_payload)
                    if response.status_code != 200:
                        raise Exception("Email service failed", response.text)
                    
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
    def post(self, request, verify_id):
        verify_token = get_object_or_404(VerifyToken, id=verify_id)
        user = get_object_or_404(WaletUser, id=verify_token.user_id)
        if user.is_active:
            return Response({"detail": "user already activated"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            user.is_active = True
            verify_token.delete()
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

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)