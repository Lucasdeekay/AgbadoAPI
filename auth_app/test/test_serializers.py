# authentication/test_serializers.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers

# Import models, serializers, and external utilities
from auth_app.models import User, KYC, OTP, Referral
from auth_app.serializers import (
    UserSerializer, KYCSerializer, OTPSerializer, ReferralSerializer
)
from auth_app.utils import generate_unique_referral_code
from wallet_app.services import update_bvn_on_reserved_account

class SerializerTests(TestCase):
    """Base test case for all serializer tests."""
    def setUp(self):
        self.user_model = get_user_model()
        self.factory = APIRequestFactory()

        # Create a user for testing
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'phone_number': '2348012345678',
            'state': 'Lagos'
        }
        self.user = self.user_model.objects.create_user(**self.user_data)

class UserSerializerTests(SerializerTests):
    """
    Tests for the UserSerializer.
    """
    @patch('auth_app.serializers.upload_to_cloudinary')
    @patch('auth_app.serializers.generate_unique_referral_code', return_value='TESTCODE')
    def test_create_user_success(self, mock_referral_code, mock_upload):
        """Test successful user creation with a unique email and phone number."""
        mock_upload.return_value = 'http://test.url/image.jpg'
        
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'phone_number': '2348012345679',
            'state': 'Ogun',
            'profile_picture': SimpleUploadedFile('profile.jpg', b'my_content', content_type='image/jpeg')
        }

        request = self.factory.post('/users/', data=data, format='multipart')
        serializer = UserSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertIsInstance(user, self.user_model)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpassword123'))
        self.assertEqual(user.profile_picture, 'http://test.url/image.jpg')
        self.assertEqual(user.referral_code, 'TESTCODE')
        mock_upload.assert_called_once()
        mock_referral_code.assert_called_once()

    def test_validate_email_uniqueness(self):
        """Test validation for unique email."""
        # Test with a unique email (should be valid)
        unique_data = {
            'email': 'anotheruser@example.com',
            'password': 'somepassword',
            'phone_number': '2341111111111',
            'state': 'Rivers'
        }
        serializer = UserSerializer(data=unique_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Test with an existing email (should be invalid)
        duplicate_data = self.user_data.copy()
        serializer = UserSerializer(data=duplicate_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this email already exists.', str(serializer.errors))

    def test_validate_phone_number_uniqueness(self):
        """Test validation for unique phone number."""
        # Test with a unique phone number (should be valid)
        unique_data = {
            'email': 'uniquephone@example.com',
            'password': 'somepassword',
            'phone_number': '2341111111111',
            'state': 'Lagos'
        }
        serializer = UserSerializer(data=unique_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Test with an existing phone number (should be invalid)
        duplicate_data = self.user_data.copy()
        serializer = UserSerializer(data=duplicate_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('User with this phone number already exists.', str(serializer.errors))

class KYCSerializerTests(SerializerTests):
    """
    Tests for the KYCSerializer.
    """
    def setUp(self):
        super().setUp()
        self.new_user = self.user_model.objects.create_user(
            email='new_kyc_user@example.com',
            password='testpassword123',
            phone_number='2349012345678',
            state='Lagos'
        )
        self.kyc_data = {
            'user': self.new_user.id,
            'bvn': '12345678901'
        }

    def test_validate_bvn_format(self):
        """Test BVN validation for length."""
        # Test valid BVN
        data = self.kyc_data.copy()
        serializer = KYCSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Test invalid BVN (wrong length)
        data['bvn'] = '12345'
        serializer = KYCSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('BVN must be exactly 11 digits.', str(serializer.errors))

    @patch('auth_app.serializers.update_bvn_on_reserved_account')
    def test_create_kyc_with_bvn_calls_service(self, mock_update_bvn):
        """Test that creating a KYC with a BVN calls the service."""
        serializer = KYCSerializer(data=self.kyc_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        kyc = serializer.save()
        mock_update_bvn.assert_called_once_with(self.new_user, '12345678901')
        self.assertIsInstance(kyc, KYC)

    @patch('auth_app.serializers.update_bvn_on_reserved_account', side_effect=ValueError('Invalid BVN'))
    def test_create_kyc_bvn_service_error(self, mock_update_bvn):
        """Test that BVN service errors are raised as ValidationErrors."""
        serializer = KYCSerializer(data=self.kyc_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.save()
        
        self.assertIn("'bvn':", str(context.exception.detail))
        mock_update_bvn.assert_called_once()

    @patch('auth_app.serializers.upload_to_cloudinary', return_value='http://doc.url/national_id.jpg')
    @patch('auth_app.serializers.update_bvn_on_reserved_account')
    def test_create_kyc_with_documents(self, mock_update_bvn, mock_upload):
        """Test creating KYC with document uploads."""
        mock_update_bvn.return_value = None  # Ensure this mock returns successfully
        data = {
            'user': self.new_user.id,
            'bvn': '12345678901',
            'national_id': SimpleUploadedFile(
                'national_id.jpg', b'my_content', content_type='image/jpeg'
            )
        }
        request = self.factory.post('/kyc/', data=data, format='multipart')
        serializer = KYCSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        kyc = serializer.save()
        self.assertEqual(kyc.national_id, 'http://doc.url/national_id.jpg')
        mock_upload.assert_called_once()
        
class OTPSerializerTests(SerializerTests):
    """
    Tests for the OTPSerializer.
    """
    def setUp(self):
        super().setUp()
        self.otp_data = {
            'user': self.user.id,
            'otp': '123456'
        }
        self.otp_instance = OTP.objects.create(user=self.user, otp='123456')

    def test_validate_otp_format(self):
        """Test OTP validation for a 6-digit number."""
        # Test valid OTP
        data = self.otp_data.copy()
        serializer = OTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test invalid OTP (wrong length)
        data['otp'] = '12345'
        serializer = OTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('OTP must be exactly 6 digits.', str(serializer.errors))

class ReferralSerializerTests(SerializerTests):
    """
    Tests for the ReferralSerializer.
    """
    def setUp(self):
        super().setUp()
        self.referer_user = self.user_model.objects.create_user(
            email='referer@example.com',
            phone_number='2349098765432',
            state='Oyo'
        )
        self.referral_instance = Referral.objects.create(
            user=self.user,
            referer=self.referer_user
        )

    def test_referral_serialization(self):
        """Test that the ReferralSerializer correctly serializes data."""
        serializer = ReferralSerializer(self.referral_instance)
        data = serializer.data
        
        # Test top-level fields
        self.assertEqual(data['id'], self.referral_instance.id)

        # Test nested user data
        self.assertEqual(data['user']['id'], self.user.id)
        self.assertEqual(data['user']['email'], self.user.email)
        self.assertEqual(data['user']['first_name'], self.user.first_name)
        self.assertEqual(data['user']['last_name'], self.user.last_name)
        self.assertEqual(data['user']['profile_picture'], self.user.profile_picture)
        
        # Test nested referer data
        self.assertEqual(data['referer']['id'], self.referer_user.id)
        self.assertEqual(data['referer']['email'], self.referer_user.email)
        self.assertEqual(data['referer']['first_name'], self.referer_user.first_name)
        self.assertEqual(data['referer']['last_name'], self.referer_user.last_name)
        self.assertEqual(data['referer']['profile_picture'], self.referer_user.profile_picture)
