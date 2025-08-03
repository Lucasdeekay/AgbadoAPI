"""
Tests for auth_app models, serializers, and views.

This module contains comprehensive tests for authentication-related functionality
including user management, KYC verification, OTP handling, and referrals.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta

from .models import User, KYC, OTP, Referral, WebAuthnCredential
from .serializers import (
    UserSerializer, KYCSerializer, OTPSerializer, ReferralSerializer
)

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State",
            first_name="Test",
            last_name="User"
        )

    def test_user_creation(self):
        """Test that a user can be created."""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.phone_number, "1234567890")
        self.assertEqual(self.user.state, "Test State")
        self.assertFalse(self.user.is_service_provider)
        self.assertFalse(self.user.is_verified)

    def test_user_string_representation(self):
        """Test the string representation of a user."""
        self.assertEqual(str(self.user), "test@example.com")

    def test_user_full_name(self):
        """Test getting user's full name."""
        self.assertEqual(self.user.get_full_name(), "Test User")

    def test_user_short_name(self):
        """Test getting user's short name."""
        self.assertEqual(self.user.get_short_name(), "Test")

    def test_user_without_names(self):
        """Test user without first/last names."""
        user = User.objects.create_user(
            email="no_name@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        self.assertEqual(user.get_full_name(), "no_name@example.com")
        self.assertEqual(user.get_short_name(), "no_name@example.com")

    def test_unique_email_constraint(self):
        """Test that email must be unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com",
                password="testpass123",
                phone_number="1111111111",
                state="Test State"
            )

    def test_unique_phone_constraint(self):
        """Test that phone number must be unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="different@example.com",
                password="testpass123",
                phone_number="1234567890",
                state="Test State"
            )


class KYCModelTest(TestCase):
    """Test cases for KYC model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.kyc = KYC.objects.create(
            user=self.user,
            national_id="https://example.com/national_id.jpg",
            bvn="12345678901",
            driver_license="https://example.com/driver_license.jpg",
            proof_of_address="https://example.com/proof_of_address.jpg"
        )

    def test_kyc_creation(self):
        """Test that a KYC record can be created."""
        self.assertEqual(self.kyc.user, self.user)
        self.assertEqual(self.kyc.status, "Pending")
        self.assertIsNotNone(self.kyc.national_id)
        self.assertIsNotNone(self.kyc.bvn)

    def test_kyc_string_representation(self):
        """Test the string representation of a KYC record."""
        expected = f"KYC for {self.user.email} - Pending"
        self.assertEqual(str(self.kyc), expected)

    def test_kyc_is_complete(self):
        """Test KYC completeness check."""
        self.assertTrue(self.kyc.is_complete())

    def test_kyc_incomplete(self):
        """Test KYC completeness with missing documents."""
        incomplete_kyc = KYC.objects.create(
            user=User.objects.create_user(
                email="incomplete@example.com",
                password="testpass123",
                phone_number="1111111111",
                state="Test State"
            ),
            national_id="https://example.com/national_id.jpg"
        )
        self.assertFalse(incomplete_kyc.is_complete())

    def test_one_to_one_relationship(self):
        """Test that a user can only have one KYC record."""
        with self.assertRaises(Exception):
            KYC.objects.create(user=self.user)


class OTPModelTest(TestCase):
    """Test cases for OTP model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.otp = OTP.objects.create(
            user=self.user,
            otp="123456"
        )

    def test_otp_creation(self):
        """Test that an OTP can be created."""
        self.assertEqual(self.otp.user, self.user)
        self.assertEqual(self.otp.otp, "123456")
        self.assertFalse(self.otp.is_used)
        self.assertIsNotNone(self.otp.expires_at)

    def test_otp_string_representation(self):
        """Test the string representation of an OTP."""
        expected = f"OTP for {self.user.email} - Not Used"
        self.assertEqual(str(self.otp), expected)

    def test_otp_expiration(self):
        """Test OTP expiration."""
        # Create an expired OTP
        expired_otp = OTP.objects.create(
            user=self.user,
            otp="654321",
            expires_at=timezone.now() - timedelta(hours=2)
        )
        self.assertTrue(expired_otp.is_expired())
        self.assertFalse(self.otp.is_expired())

    def test_otp_used_status(self):
        """Test OTP used status."""
        self.otp.is_used = True
        self.otp.save()
        expected = f"OTP for {self.user.email} - Used"
        self.assertEqual(str(self.otp), expected)


class ReferralModelTest(TestCase):
    """Test cases for Referral model."""

    def setUp(self):
        """Set up test data."""
        self.referer = User.objects.create_user(
            email="referer@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        self.referral = Referral.objects.create(
            user=self.user,
            referer=self.referer
        )

    def test_referral_creation(self):
        """Test that a referral can be created."""
        self.assertEqual(self.referral.user, self.user)
        self.assertEqual(self.referral.referer, self.referer)

    def test_referral_string_representation(self):
        """Test the string representation of a referral."""
        expected = f"{self.user.email} referred by {self.referer.email}"
        self.assertEqual(str(self.referral), expected)

    def test_unique_referral_constraint(self):
        """Test that a user can only be referred once by the same referer."""
        with self.assertRaises(Exception):
            Referral.objects.create(
                user=self.user,
                referer=self.referer
            )


class WebAuthnCredentialModelTest(TestCase):
    """Test cases for WebAuthnCredential model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.credential = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id="test_credential_id_12345",
            public_key="test_public_key_data",
            transports="usb,nfc"
        )

    def test_credential_creation(self):
        """Test that a WebAuthn credential can be created."""
        self.assertEqual(self.credential.user, self.user)
        self.assertEqual(self.credential.credential_id, "test_credential_id_12345")
        self.assertEqual(self.credential.sign_count, 0)

    def test_credential_string_representation(self):
        """Test the string representation of a credential."""
        expected = f"Credential for {self.user.email} - ID: test_credent..."
        self.assertEqual(str(self.credential), expected)


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State",
            first_name="Test",
            last_name="User"
        )
        self.serializer = UserSerializer(instance=self.user)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'state', 'is_service_provider', 'is_verified', 'date_joined',
            'profile_picture', 'referral_code', 'is_busy', 'pin'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_email_field_content(self):
        """Test the email field content."""
        data = self.serializer.data
        self.assertEqual(data['email'], self.user.email)

    def test_phone_number_field_content(self):
        """Test the phone number field content."""
        data = self.serializer.data
        self.assertEqual(data['phone_number'], self.user.phone_number)

    def test_validate_email_uniqueness(self):
        """Test email uniqueness validation."""
        serializer = UserSerializer()
        with self.assertRaises(Exception):
            serializer.validate_email("test@example.com")

    def test_validate_phone_number_uniqueness(self):
        """Test phone number uniqueness validation."""
        serializer = UserSerializer()
        with self.assertRaises(Exception):
            serializer.validate_phone_number("1234567890")


class KYCSerializerTest(TestCase):
    """Test cases for KYCSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.kyc = KYC.objects.create(
            user=self.user,
            national_id="https://example.com/national_id.jpg",
            bvn="12345678901"
        )
        self.serializer = KYCSerializer(instance=self.kyc)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'user', 'national_id', 'bvn', 'driver_license',
            'proof_of_address', 'status', 'updated_at', 'verified_at'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_bvn_validation(self):
        """Test BVN format validation."""
        serializer = KYCSerializer()
        # Test valid BVN
        valid_bvn = serializer.validate_bvn("12345678901")
        self.assertEqual(valid_bvn, "12345678901")
        
        # Test invalid BVN
        with self.assertRaises(Exception):
            serializer.validate_bvn("1234567890")  # Too short


class OTPSerializerTest(TestCase):
    """Test cases for OTPSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.otp = OTP.objects.create(
            user=self.user,
            otp="123456"
        )
        self.serializer = OTPSerializer(instance=self.otp)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'otp', 'created_at', 'expires_at', 'is_used'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_otp_validation(self):
        """Test OTP format validation."""
        serializer = OTPSerializer()
        # Test valid OTP
        valid_otp = serializer.validate_otp("123456")
        self.assertEqual(valid_otp, "123456")
        
        # Test invalid OTP
        with self.assertRaises(Exception):
            serializer.validate_otp("12345")  # Too short


class ReferralSerializerTest(TestCase):
    """Test cases for ReferralSerializer."""

    def setUp(self):
        """Set up test data."""
        self.referer = User.objects.create_user(
            email="referer@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        self.referral = Referral.objects.create(
            user=self.user,
            referer=self.referer
        )
        self.serializer = ReferralSerializer(instance=self.referral)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'referer', 'created_at'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_user_field_content(self):
        """Test the user field content."""
        data = self.serializer.data
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], self.user.email)

    def test_referer_field_content(self):
        """Test the referer field content."""
        data = self.serializer.data
        self.assertIn('referer', data)
        self.assertEqual(data['referer']['email'], self.referer.email)


class AuthAppViewsTest(APITestCase):
    """Test cases for auth app views."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'phone_number': '1111111111',
            'state': 'New State',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)

    def test_user_login(self):
        """Test user login endpoint."""
        url = reverse('login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_user_profile_update(self):
        """Test user profile update endpoint."""
        url = reverse('update_profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'state': 'Updated State'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')

    def test_kyc_submission(self):
        """Test KYC submission endpoint."""
        url = reverse('submit_kyc')
        data = {
            'bvn': '12345678901'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('kyc', response.data)

    def test_otp_verification(self):
        """Test OTP verification endpoint."""
        # Create an OTP first
        otp = OTP.objects.create(
            user=self.user,
            otp="123456"
        )
        
        url = reverse('verify_otp')
        data = {
            'otp': '123456'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthAppViewSetsTest(APITestCase):
    """Test cases for auth app ViewSets."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create test data
        self.kyc = KYC.objects.create(
            user=self.user,
            bvn="12345678901"
        )
        self.otp = OTP.objects.create(
            user=self.user,
            otp="123456"
        )

    def test_user_list(self):
        """Test listing users."""
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_detail(self):
        """Test getting user details."""
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_kyc_list(self):
        """Test listing KYC records."""
        url = reverse('kyc-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_kyc_detail(self):
        """Test getting KYC details."""
        url = reverse('kyc-detail', args=[self.kyc.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)

    def test_otp_list(self):
        """Test listing OTP records."""
        url = reverse('otp-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_otp_detail(self):
        """Test getting OTP details."""
        url = reverse('otp-detail', args=[self.otp.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)