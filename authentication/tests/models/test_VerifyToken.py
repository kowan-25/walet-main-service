import uuid
from django.test import TestCase

from authentication.models import VerifyToken

class VerifyTokenModelTest(TestCase):
    def test_create_verify_token(self):
        """
        Test the creation of a VerifyToken instance.
        """
        token = VerifyToken.objects.create(user_id=uuid.uuid4())
        self.assertTrue(isinstance(token, VerifyToken))
        self.assertIsInstance(token.id, uuid.UUID)
        self.assertFalse(token._meta.get_field('id').editable)
        self.assertIsInstance(token.user_id, uuid.UUID)
        self.assertFalse(token._meta.get_field('user_id').editable)
