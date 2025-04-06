from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from authentication.models import WaletUser
from authentication.serializers import CustomTokenObtainPairSerializer, RegisterUserSerializer
from rest_framework_simplejwt.tokens import AccessToken

class RegisterUserSerializerTest(TestCase):

    def test_valid_registration(self):
        """
        Test successful user registration with valid data.
        """
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!"
        }
        serializer = RegisterUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertIsInstance(user, WaletUser)
        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.email, data["email"])
        self.assertNotEqual(user.password, data["password"])  # hashed
        self.assertTrue(user.check_password(data["password"]))

    def test_missing_number_in_password_should_fail(self):
        """
        Test that registration fails when the password lacks a number.
        """
        data = {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "NoNumber!"
        }
        serializer = RegisterUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Password must contain at least one number.", str(serializer.errors))

    def test_password_write_only(self):
        """
        Test that the password field is write-only and not returned in serialized data.
        """
        data = {
            "username": "secureuser",
            "email": "secure@example.com",
            "password": "Strong123!"
        }
        serializer = RegisterUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        serialized_data = RegisterUserSerializer(user).data
        self.assertNotIn("password", serialized_data)

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
