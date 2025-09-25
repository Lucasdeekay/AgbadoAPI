# authentication/test_admin.py
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Import the models and the admin classes
from auth_app.models import User, KYC, OTP, Referral, WebAuthnCredential
from auth_app.admin import (
    UserAdmin, KYCAdmin, OTPAdmin, ReferralAdmin, WebAuthnCredentialAdmin
)

class MockRequest:
    """A mock request object for testing admin methods."""
    pass

class AdminTests(TestCase):
    """
    Tests for the admin interface configurations.
    """
    def setUp(self):
        # Create a superuser to access the admin site
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='adminpassword',
            phone_number='2341234567890',
            state='Lagos'
        )
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            phone_number='2349012345678',
            state='Ogun'
        )

        # Create model instances for testing
        self.kyc_instance = KYC.objects.create(user=self.user)
        self.otp_instance = OTP.objects.create(user=self.user, otp='12345')
        self.referer_user = get_user_model().objects.create_user(
            email='referer@example.com',
            phone_number='2348011111111',
            state='Oyo'
        )
        self.referral_instance = Referral.objects.create(
            user=self.user, referer=self.referer_user
        )
        self.webauthn_instance = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id='test-id-12345678901234567890abcdef',
            public_key='test-public-key'
        )
        
        # Instantiate admin site and model admin classes
        self.site = AdminSite()
        self.user_admin = UserAdmin(User, self.site)
        self.kyc_admin = KYCAdmin(KYC, self.site)
        self.otp_admin = OTPAdmin(OTP, self.site)
        self.referral_admin = ReferralAdmin(Referral, self.site)
        self.webauthn_admin = WebAuthnCredentialAdmin(WebAuthnCredential, self.site)

    def test_user_admin_list_display(self):
        """Test the list_display fields for UserAdmin."""
        self.assertListEqual(
            list(self.user_admin.list_display),
            ['email', 'get_full_name', 'phone_number', 'state', 'is_active',
             'is_service_provider', 'is_verified', 'is_busy', 'date_joined']
        )
    
    def test_user_admin_get_full_name(self):
        """Test the get_full_name custom method."""
        self.assertEqual(self.user_admin.get_full_name(self.user), self.user.get_full_name())

    def test_user_admin_queryset(self):
        """Test that get_queryset uses select_related for UserAdmin."""
        request = MockRequest()
        queryset = self.user_admin.get_queryset(request)
        # Verify that accessing a related field on the queryset does not cause a new query
        with self.assertNumQueries(1):
            list(queryset.values('id', 'groups__name'))

class KYCAdminTests(TestCase):
    """
    Tests for the KYCAdmin.
    """
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            phone_number='2349012345678',
            state='Ogun'
        )
        self.kyc_admin = KYCAdmin(KYC, AdminSite())

    def test_kyc_admin_get_user_email(self):
        """Test the get_user_email custom method."""
        kyc_instance = KYC.objects.create(user=self.user)
        self.assertEqual(self.kyc_admin.get_user_email(kyc_instance), 'testuser@example.com')

    def test_kyc_admin_get_document_count(self):
        """Test the get_document_count custom method."""
        kyc_instance_partial = KYC.objects.create(
            user=self.user, national_id='doc.jpg', bvn='12345678901'
        )
        kyc_instance_full = KYC.objects.create(
            user=get_user_model().objects.create_user(
                email='full@example.com',
                phone_number='2349012345679',
                state='Ogun'
            ),
            national_id='doc.jpg',
            driver_license='license.jpg',
            proof_of_address='proof.pdf',
            bvn='12345678901'
        )
        self.assertEqual(self.kyc_admin.get_document_count(kyc_instance_partial), '2/4')
        self.assertEqual(self.kyc_admin.get_document_count(kyc_instance_full), '4/4')

    def test_kyc_admin_queryset(self):
        """Test that get_queryset uses select_related."""
        request = MockRequest()
        queryset = self.kyc_admin.get_queryset(request)
        self.assertEqual(queryset.query.select_related, {'user': {}})


class OTPAdminTests(TestCase):
    """
    Tests for the OTPAdmin.
    """
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            phone_number='2349012345678',
            state='Ogun'
        )
        self.otp_admin = OTPAdmin(OTP, AdminSite())

    def test_otp_admin_is_expired_display_valid(self):
        """Test the is_expired_display method for a valid OTP."""
        valid_otp = OTP.objects.create(user=self.user, otp='12345')
        # Check that the output contains the 'green' color
        self.assertIn('green', self.otp_admin.is_expired_display(valid_otp))

    def test_otp_admin_is_expired_display_expired(self):
        """Test the is_expired_display method for an expired OTP."""
        expired_otp = OTP.objects.create(user=self.user, otp='54321',
                                          expires_at=timezone.now() - timedelta(minutes=1))
        # Check that the output contains the 'red' color
        self.assertIn('red', self.otp_admin.is_expired_display(expired_otp))

    def test_otp_admin_queryset(self):
        """Test that get_queryset uses select_related."""
        request = MockRequest()
        queryset = self.otp_admin.get_queryset(request)
        self.assertEqual(queryset.query.select_related, {'user': {}})


class ReferralAdminTests(TestCase):
    """
    Tests for the ReferralAdmin.
    """
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            phone_number='2349012345678',
            state='Ogun'
        )
        self.referer = get_user_model().objects.create_user(
            email='referer@example.com',
            phone_number='2348011111111',
            state='Oyo'
        )
        self.referral = Referral.objects.create(user=self.user, referer=self.referer)
        self.referral_admin = ReferralAdmin(Referral, AdminSite())

    def test_referral_admin_get_user_email(self):
        """Test the get_user_email custom method."""
        self.assertEqual(self.referral_admin.get_user_email(self.referral), 'testuser@example.com')

    def test_referral_admin_get_referer_email(self):
        """Test the get_referer_email custom method."""
        self.assertEqual(self.referral_admin.get_referer_email(self.referral), 'referer@example.com')

    def test_referral_admin_queryset(self):
        """Test that get_queryset uses select_related for both user and referer."""
        request = MockRequest()
        queryset = self.referral_admin.get_queryset(request)
        self.assertEqual(queryset.query.select_related, {'user': {}, 'referer': {}})


class WebAuthnCredentialAdminTests(TestCase):
    """
    Tests for the WebAuthnCredentialAdmin.
    """
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            phone_number='2349012345678',
            state='Ogun'
        )
        self.credential = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id='test-id-12345678901234567890abcdef',
            public_key='test-public-key'
        )
        self.webauthn_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    def test_webauthn_admin_credential_id_short(self):
        """Test the credential_id_short custom method."""
        short_id = self.webauthn_admin.credential_id_short(self.credential)
        self.assertIn('test-id-123456789012...', short_id)

    def test_webauthn_admin_queryset(self):
        """Test that get_queryset uses select_related."""
        request = MockRequest()
        queryset = self.webauthn_admin.get_queryset(request)
        self.assertEqual(queryset.query.select_related, {'user': {}})
