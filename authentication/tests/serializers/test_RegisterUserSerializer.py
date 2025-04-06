from django.test import TestCase

from authentication.models import WaletUser
from authentication.serializers import RegisterUserSerializer

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