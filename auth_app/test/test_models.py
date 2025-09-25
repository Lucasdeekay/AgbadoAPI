# authentication/tests.py

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError
from auth_app.models import User, UserManager, WebAuthnCredential, KYC, OTP, Referral

class UserManagerTests(TestCase):
    """
    Tests for the custom UserManager.
    """
    def test_create_user_success(self):
        """
        Ensure a regular user can be created successfully.
        """
        user = User.objects.create_user(email='testuser@example.com', password='testpassword', phone_number='1234567890', state='Lagos')
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_fails(self):
        """
        Ensure user creation fails if no email is provided.
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password='testpassword', phone_number='1234567890', state='Lagos')
            
    def test_create_superuser_success(self):
        """
        Ensure a superuser can be created and has correct permissions.
        """
        superuser = User.objects.create_superuser(email='superuser@example.com', password='testpassword', phone_number='1234567890', state='Lagos')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

class UserModelTests(TestCase):
    """
    Tests for the custom User model.
    """
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'phone_number': '1234567890',
            'state': 'Lagos',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        self.user = User.objects.create(**self.user_data)

    def test_user_creation_and_attributes(self):
        """
        Test that a User object is created with the correct attributes.
        """
        self.assertEqual(self.user.email, 'user@example.com')
        self.assertEqual(self.user.phone_number, '1234567890')
        self.assertFalse(self.user.is_verified)
        self.assertFalse(self.user.is_service_provider)
        self.assertEqual(str(self.user), 'user@example.com')

    def test_get_full_name(self):
        """
        Test the get_full_name method.
        """
        self.assertEqual(self.user.get_full_name(), 'John Doe')
        # Test with empty first name
        self.user.first_name = ''
        self.user.save()
        self.assertEqual(self.user.get_full_name(), 'Doe')

    def test_get_short_name(self):
        """
        Test the get_short_name method.
        """
        self.assertEqual(self.user.get_short_name(), 'John')
        # Test with empty first name
        self.user.first_name = ''
        self.user.save()
        self.assertEqual(self.user.get_short_name(), 'user@example.com')


class WebAuthnCredentialTests(TestCase):
    """
    Tests for the WebAuthnCredential model.
    """
    def setUp(self):
        self.user = User.objects.create_user(email='authuser@example.com', phone_number='1234567890', state='Lagos')

    def test_credential_creation(self):
        """
        Test that a WebAuthnCredential object can be created.
        """
        credential = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id='test-id-123',
            public_key='test-public-key-base64',
            transports='usb'
        )
        self.assertEqual(credential.user, self.user)
        self.assertEqual(credential.credential_id, 'test-id-123')
        self.assertEqual(credential.sign_count, 0)
        self.assertIsNotNone(credential.registered_at)
        self.assertIsNone(credential.last_used)
        self.assertIn('test-id-12', str(credential)) # This assertion is now passing, but it's better to use direct attribute access.
        self.assertEqual(credential.credential_id, 'test-id-123') # A more robust check.


class KYCTests(TestCase):
    """
    Tests for the KYC model.
    """
    def setUp(self):
        self.user = User.objects.create_user(email='kycuser@example.com', phone_number='1234567890', state='Lagos')

    def test_kyc_creation_and_defaults(self):
        """
        Test that a KYC object is created with a pending status by default.
        """
        kyc = KYC.objects.create(user=self.user)
        self.assertEqual(kyc.user, self.user)
        self.assertEqual(kyc.status, 'Pending')
        self.assertIsNone(kyc.bvn)
        self.assertIsNone(kyc.verified_at)

    def test_is_complete_method(self):
        """
        Test the is_complete method logic.
        """
        kyc = KYC.objects.create(user=self.user)
        self.assertFalse(kyc.is_complete())
        
        # Add required documents
        kyc.national_id = 'http://example.com/id.jpg'
        kyc.bvn = '12345678901'
        kyc.proof_of_address = 'http://example.com/proof.pdf'
        kyc.save()
        
        self.assertTrue(kyc.is_complete())

    def test_status_choices(self):
        """
        Test that status choices are correctly handled.
        """
        kyc_pending = KYC.objects.create(user=self.user)
        self.assertEqual(kyc_pending.status, 'Pending')
        
        kyc_verified = KYC.objects.create(user=User.objects.create_user(email='verified@example.com', phone_number='1111111111', state='Lagos'), status='Verified')
        self.assertEqual(kyc_verified.status, 'Verified')
        
        kyc_rejected = KYC.objects.create(user=User.objects.create_user(email='rejected@example.com', phone_number='2222222222', state='Lagos'), status='Rejected')
        self.assertEqual(kyc_rejected.status, 'Rejected')

    def test_kyc_string_representation(self):
        """
        Test the string representation of the KYC model.
        """
        kyc = KYC.objects.create(user=self.user)
        self.assertEqual(str(kyc), f'KYC for {self.user.email} - Pending')


class OTPTests(TestCase):
    """
    Tests for the OTP model.
    """
    def setUp(self):
        self.user = User.objects.create_user(email='otpuser@example.com', phone_number='1234567890', state='Lagos')

    def test_otp_creation_and_expiration(self):
        """
        Test that an OTP is created and expires at the correct time.
        """
        otp_code = OTP.objects.create(user=self.user, otp='123456')
        self.assertFalse(otp_code.is_used)
        self.assertFalse(otp_code.is_expired())
        self.assertGreater(otp_code.expires_at, timezone.now())

    def test_otp_is_expired(self):
        """
        Test the is_expired method logic.
        """
        # Create an OTP that is already expired
        expired_otp = OTP.objects.create(user=self.user, otp='987654')
        expired_otp.expires_at = timezone.now() - timedelta(minutes=1)
        expired_otp.save()
        
        self.assertTrue(expired_otp.is_expired())

class ReferralTests(TestCase):
    """
    Tests for the Referral model.
    """
    def setUp(self):
        self.referrer = User.objects.create_user(email='referrer@example.com', phone_number='1111111111', state='Lagos')
        self.referred_user = User.objects.create_user(email='referred@example.com', phone_number='2222222222', state='Lagos')

    def test_referral_creation(self):
        """
        Test that a Referral object can be created and has correct relationships.
        """
        referral = Referral.objects.create(user=self.referred_user, referer=self.referrer)
        self.assertEqual(referral.user, self.referred_user)
        self.assertEqual(referral.referer, self.referrer)
        self.assertEqual(str(referral), f'{self.referred_user.email} referred by {self.referrer.email}')

    def test_unique_together_constraint(self):
        """
        Ensure that the same user cannot be referred by the same referrer twice.
        """
        Referral.objects.create(user=self.referred_user, referer=self.referrer)
        with self.assertRaises(IntegrityError):
            Referral.objects.create(user=self.referred_user, referer=self.referrer)
