from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from authentication.models import WaletUser
from authentication.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken

class CustomTokenObtainPairSerializerTest(TestCase):

    def setUp(self):
        self.user = WaletUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Test123!"
        )
        self.user.is_active = True
        self.user.save()

    def test_token_contains_custom_claims(self):
        """
        Test that the generated JWT access token includes custom claims (user_id and username).
        """
        serializer = CustomTokenObtainPairSerializer(data={
            "username": "testuser",
            "password": "Test123!"
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        tokens = serializer.validated_data

        access_token = tokens["access"]
        refresh_token = tokens["refresh"]

        decoded_access = AccessToken(access_token)

        self.assertEqual(str(self.user.id), decoded_access["user_id"])
        self.assertEqual(self.user.username, decoded_access["username"])
