import uuid
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from authentication.models import WaletUser, VerifyToken

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

class WaletUserModelTest(TestCase):
    def setUp(self):
        self.user = WaletUser.objects.create(
            username='testuser',
            email='test@example.com',
            password='ValidPassword!1'  # valid password
        )
        self.user.is_active = True

    def test_user_creation(self):
        """
        Test basic user creation and attributes.
        """
        self.assertEqual(str(self.user), 'testuser')
        self.assertIsInstance(self.user.id, uuid.UUID)
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_deleted)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(self.user.is_active)
        self.assertIsNotNone(self.user.created_at)
        self.assertIsNone(self.user.deleted_at)

    def test_username_unique_constraint(self):
        """
        Test that the username field has a unique constraint.
        """
        with self.assertRaises(Exception) as context: 
            WaletUser.objects.create(
                username='testuser', 
                email='new@example.com',
                password='anotherpassword'
            )
        self.assertTrue(isinstance(context.exception, Exception)) 


    def test_email_unique_constraint(self):
        """
        Test that the email field has a unique constraint.
        """
        with self.assertRaises(Exception) as context: 
            WaletUser.objects.create(
                username='newuser',
                email='test@example.com',  
                password='anotherpassword'
            )
        self.assertTrue(isinstance(context.exception, Exception)) 

    def test_password_validation_length(self):
        """
        Test password validation: minimum length.
        """
        user = WaletUser.objects.create(username='shortpass', email='shortpass@example.com', password='short')
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn('Password must be at least 8 characters long.', context.exception.messages)

    def test_password_validation_number(self):
        """
        Test password validation: must contain a number.
        """
        user = WaletUser.objects.create(username='nonumber', email='nonumber@example.com', password='NoNumber!')
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn('Password must contain at least one number.', context.exception.messages)

    def test_password_validation_special_char(self):
        """
        Test password validation: must contain a special character.
        """
        user = WaletUser.objects.create(username='nospecial', email='nospecial@example.com', password='NoSpecial1')
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn('Password must contain at least one special character.', context.exception.messages)

    def test_has_perm(self):
        """
        Test the has_perm method.
        """
        self.assertFalse(self.user.has_perm('some.permission'))
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.has_perm('some.permission')) 

    def test_has_module_perms(self):
        """
        Test the has_module_perms method.
        """
        self.assertFalse(self.user.has_module_perms('some_app')) 
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.has_module_perms('some_app')) 
    
    def test_clean_method(self):
        """
        Test the clean method for password validation.
        """
        user = WaletUser(username="testclean", email="clean@example.com", password="short")
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn("Password must be at least 8 characters long.", context.exception.messages)

        user.password = "validpassword"
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn("Password must contain at least one number.", context.exception.messages)
        
        user.password = "validpassword1"
        with self.assertRaises(ValidationError) as context:
            user.clean()
        self.assertIn("Password must contain at least one special character.", context.exception.messages)

        user.password = "ValidPassword!1"
        try:
            user.clean() 
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for a valid password.")
        

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
