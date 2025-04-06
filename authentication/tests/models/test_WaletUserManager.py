from django.test import TestCase

from authentication.models import WaletUser

class WaletUserManagerTest(TestCase):
    def test_create_user(self):
        """
        Test the create_user method of WaletUserManager.
        """
        user = WaletUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active) #important
        self.assertIsNotNone(user.created_at)

    def test_create_user_no_email(self):
        """
        Test that create_user raises a ValueError when no email is provided.
        """
        with self.assertRaises(ValueError) as context:
            WaletUser.objects.create_user(username='testuser', email='')
        self.assertEqual(str(context.exception), "The Email field must be set")

    def test_create_superuser(self):
        """
        Test the create_superuser method of WaletUserManager.
        """
        superuser = WaletUser.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertEqual(superuser.username, 'adminuser')
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.check_password('adminpassword'))
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active) #important
        self.assertIsNotNone(superuser.created_at)