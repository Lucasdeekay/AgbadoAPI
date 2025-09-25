import base64
import json
from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.conf import settings
from faker import Faker

from auth_app.models import User as CustomUser, OTP, Referral, WebAuthnCredential
from user_app.models import UserReward
from django.db import transaction, DatabaseError

# Initialize Faker for generating test data
fake = Faker()


class AuthViewsTest(APITestCase):
    """
    Test suite for the authentication API views.
    """

    def setUp(self):
        """
        Set up common data for tests.
        """
        self.user_data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number(),
            "password": "password123",
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Mock external functions to prevent network calls
        self.mock_send_email = mock.patch('auth_app.views.send_otp_email').start()
        self.mock_send_sms = mock.patch('auth_app.views.send_otp_sms').start()
        
        # Define URLs for easier access
        self.register_sp_url = reverse('register-service-provider')
        self.register_user_url = reverse('register-user')
        self.send_otp_url = reverse('send-otp')
        self.verify_otp_url = reverse('verify-otp')
        self.pin_reg_url = reverse('pin-register')
        self.pin_update_url = reverse('pin-update')
        self.pin_auth_url = reverse('pin-auth')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.forgot_password_url = reverse('forgot-password')
        self.reset_password_url = reverse('reset-password')
        self.update_busy_url = reverse('update-status')
        self.google_apple_auth_url = reverse('google-or-apple-auth')
        self.start_webauthn_url = reverse('webauthn-register-start')

        # New WebAuthn and Account URLs
        self.complete_webauthn_reg_url = reverse('webauthn-register-complete')
        self.start_webauthn_auth_url = reverse('webauthn-login-start')
        self.complete_webauthn_auth_url = reverse('webauthn-login-complete')
        self.list_webauthn_url = reverse('webauthn-credentials-list')
        self.delete_account_url = reverse('delete-account')
        self.delete_webauthn_url_name = 'webauthn-credential-delete'

    def tearDown(self):
        """
        Clean up mocks after each test.
        """
        mock.patch.stopall()

    # --- Registration Views Tests ---

    def test_register_service_provider_success(self):
        """
        Test successful registration of a service provider.
        """
        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": "9998887776",
            "password": "newpassword123",
            "state": "Lagos",
        }
        response = self.client.post(self.register_sp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('token' in response.data)
        self.assertTrue(CustomUser.objects.get(email=data['email']).is_service_provider)
        # self.mock_send_email.assert_called_once()
        # self.mock_send_sms.assert_called_once()
        
    def test_register_user_success_with_referral(self):
        """
        Test successful user registration with a valid referral code.
        """
        referer_user = CustomUser.objects.create_user(
            email=fake.email(), phone_number="1234567890", password="testpassword"
        )
        referer_user.referral_code = 'TESTCODE'
        referer_user.save()

        data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": "9998887777", # Corrected field name from phone_number to phone
            "password": "newpassword123",
            "referral_code": "TESTCODE",
        }
        response = self.client.post(self.register_user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('token' in response.data)
        self.assertTrue(Referral.objects.filter(referer=referer_user).exists())
        self.assertTrue(UserReward.objects.get(user=referer_user).points > 0)

    def test_register_user_duplicate_email(self):
        """
        Test registration fails with a duplicate email.
        """
        data = {
            "first_name": "New",
            "last_name": "User",
            "email": self.user.email,
            "phone": "9998887778",
            "password": "newpassword123",
        }
        response = self.client.post(self.register_user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A user with this email already exists.", response.data['message'])

    def test_register_user_missing_fields(self):
        """
        Test registration fails with missing required fields.
        """
        data = {
            "email": "incomplete@example.com",
            "password": "password123"
        }
        response = self.client.post(self.register_user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone number, and password are required.", response.data['message'])

    # --- OTP Views Tests ---

    def test_send_otp_success_email(self):
        """
        Test sending OTP successfully via email.
        """
        data = {"identifier": self.user.email}
        response = self.client.post(self.send_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_send_email.assert_called_once()
        self.mock_send_sms.assert_not_called()
    
    def test_verify_otp_success(self):
        """
        Test successful OTP verification.
        """
        otp_instance = OTP.objects.create(user=self.user, otp='123456')
        data = {"identifier": self.user.email, "otp": "123456"}
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.assertTrue(OTP.objects.get(id=otp_instance.id).is_used)

    def test_verify_otp_invalid(self):
        """
        Test OTP verification fails with an invalid OTP.
        """
        OTP.objects.create(user=self.user, otp='123456')
        data = {"identifier": self.user.email, "otp": "999999"}
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid OTP.", response.data['message'])

    # --- PIN Views Tests ---
    
    def test_pin_registration_success(self):
        """
        Test successful PIN registration.
        """
        data = {"pin": "123456"}
        response = self.client.post(self.pin_reg_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.pin, "123456")

    def test_pin_update_success(self):
        """
        Test successful PIN update.
        """
        self.user.pin = "111111"
        self.user.save()
        data = {"pin": "654321"}
        response = self.client.put(self.pin_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.pin, "654321")
        
    def test_pin_auth_success(self):
        """
        Test successful PIN authentication.
        """
        self.user.pin = "123456"
        self.user.save()
        data = {"pin": "123456"}
        response = self.client.post(self.pin_auth_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("PIN authentication successfully.", response.data['message'])

    def test_pin_auth_invalid(self):
        """
        Test PIN authentication fails with an invalid PIN.
        """
        self.user.pin = "123456"
        self.user.save()
        data = {"pin": "999999"}
        response = self.client.post(self.pin_auth_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid PIN.", response.data['message'])

    # --- Login & Logout Tests ---

    def test_login_success_email(self):
        """
        Test successful login with email.
        """
        self.client.credentials()  # Clear auth token
        data = {"identifier": self.user.email, "password": self.user_data['password']}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)

    def test_login_success_phone(self):
        """
        Test successful login with phone number.
        """
        self.client.credentials()
        data = {"identifier": self.user.phone_number, "password": self.user_data['password']}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)
        
    def test_logout_success(self):
        """
        Test successful logout.
        """
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    # --- Password Reset Tests ---
    
    def test_forgot_password_success(self):
        """
        Test successful forgot password request.
        """
        data = {"identifier": self.user.email}
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_send_email.assert_called_once()
        
    def test_reset_password_success(self):
        """
        Test successful password reset.
        """
        new_password = "new_secure_password"
        data = {"identifier": self.user.email, "new_password": new_password}
        response = self.client.post(self.reset_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    # --- Account Management Tests ---
    
    def test_update_is_busy_success(self):
        """
        Test successful update of `is_busy` status.
        """
        self.user.is_busy = False
        self.user.save()
        response = self.client.put(self.update_busy_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_busy'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_busy)
        
    def test_social_auth_login_existing_user(self):
        """
        Test social authentication for an existing user.
        """
        self.client.credentials()
        data = {
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        response = self.client.post(self.google_apple_auth_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login successful", response.data['message'])
        
    # --- WebAuthn Tests ---

    @mock.patch('auth_app.views.generate_registration_options')
    def test_start_webauthn_registration_success(self, mock_generate_options):
        """
        Test starting WebAuthn registration.
        """
        mock_options = mock.Mock()
        mock_options.json = {"challenge": "mock_challenge"}
        mock_options.challenge = b'mock_challenge_bytes'
        mock_generate_options.return_value = mock_options

        response = self.client.post(self.start_webauthn_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('publicKeyCredentialCreationOptions', response.data)
        self.assertEqual(self.client.session['challenge'], base64.urlsafe_b64encode(b'mock_challenge_bytes').decode('utf-8').rstrip("="))
        self.assertEqual(self.client.session['user_id_for_webauthn_reg'], str(self.user.id))

    def test_complete_webauthn_registration_success(self):
        """
        Test successful completion of WebAuthn registration.
        """
        # Correctly mock the `verify_registration_response` function
        with mock.patch('auth_app.views.verify_registration_response') as mock_verify:
            
            # Mock the session data that the view will check
            self.client.session['challenge'] = 'mocked_challenge'
            self.client.session['user_id_for_webauthn_reg'] = str(self.user.id)
            
            # Mock the verification result object the function should return
            mock_verification_result = mock.Mock()
            mock_verification_result.credential_id = b'mocked_cred_id'
            mock_verification_result.credential_public_key = b'mocked_public_key'
            mock_verification_result.sign_count = 1
            mock_verify.return_value = mock_verification_result
            
            # Provide a dummy JSON payload that the view would receive from a client
            client_data = {
                "id": "mock_cred_id",
                "rawId": "mock_raw_id",
                "response": {
                    "clientDataJSON": "mock_client_data",
                    "attestationObject": "mock_attestation_object"
                },
                "type": "public-key"
            }
            
            response = self.client.post(
                self.complete_webauthn_reg_url, 
                data=json.dumps(client_data), # Send data as JSON string
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('WebAuthn credential registered successfully.', str(response.content))
            self.assertEqual(WebAuthnCredential.objects.count(), 1)
            
            # Verify that session data has been popped
            self.assertIsNone(self.client.session.get('challenge'))
            self.assertIsNone(self.client.session.get('user_id_for_webauthn_reg'))

    def test_complete_webauthn_registration_no_challenge(self):
        """
        Test completion with a missing or invalid challenge.
        """
        response = self.client.post(
            self.complete_webauthn_reg_url, 
            data={}, 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid or expired registration challenge.', str(response.content))
        
    def test_complete_webauthn_registration_verification_failure(self):
        """
        Test registration when the verification process fails.
        """
        # Mock the verification function to raise a specific error
        with mock.patch('auth_app.views.verify_registration_response', side_effect=ValueError("Invalid signature")):
            # Set the session data to ensure the view reaches the verification step
            self.client.session['challenge'] = 'mocked_challenge'
            self.client.session['user_id_for_webauthn_reg'] = str(self.user.id)
            
            # Provide a dummy JSON payload
            client_data = {
                "id": "mock_cred_id",
                "rawId": "mock_raw_id",
                "response": {
                    "clientDataJSON": "mock_client_data",
                    "attestationObject": "mock_attestation_object"
                },
                "type": "public-key"
            }
            
            response = self.client.post(
                self.complete_webauthn_reg_url, 
                data=json.dumps(client_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('WebAuthn verification failed', str(response.content))

    def test_start_webauthn_authentication_success(self):
        """
        Test successful start of WebAuthn authentication.
        """
        # Create a credential first
        WebAuthnCredential.objects.create(
            user=self.user,
            credential_id="mocked_cred_id",
            public_key="mocked_public_key",
            sign_count=1
        )
        self.client.credentials() # Test this view as unauthenticated

        with mock.patch('auth_app.views.generate_authentication_options') as mock_generate:
            mock_options = mock.Mock()
            mock_options.challenge = b'auth_challenge'
            mock_options.json = {'challenge': 'mock_challenge_json'}
            mock_generate.return_value = mock_options
            
            response = self.client.post(
                self.start_webauthn_auth_url, 
                data={'email': self.user.email}, 
                format='json' # Correct way to pass JSON data to test client
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('publicKeyCredentialRequestOptions', response.json())
            self.assertIsNotNone(self.client.session.get('challenge'))
            self.assertEqual(self.client.session.get('user_id_for_webauthn_auth'), str(self.user.id))

    def test_start_webauthn_authentication_no_credentials(self):
        """
        Test starting authentication for a user with no credentials.
        """
        self.client.credentials() # Test this view as unauthenticated
        response = self.client.post(
            self.start_webauthn_auth_url, 
            data={'email': self.user.email}, 
            format='json' # Correct way to pass JSON data to test client
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No WebAuthn credentials registered', str(response.content))

    def test_complete_webauthn_authentication_success(self):
        """
        Test successful completion of WebAuthn authentication.
        """
        self.client.credentials() # Test this view as unauthenticated
        
        # Create a credential and set session data
        cred = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id="mocked_cred_id",
            public_key="mocked_public_key",
            sign_count=1
        )
        self.client.session['challenge'] = 'mocked_challenge'
        self.client.session['user_id_for_webauthn_auth'] = str(self.user.id)
        
        # Correctly mock the `verify_authentication_response` function
        with mock.patch('auth_app.views.verify_authentication_response') as mock_verify:
            
            # Mock verification result
            mock_verification_result = mock.Mock()
            mock_verification_result.new_sign_count = 2
            mock_verify.return_value = mock_verification_result
            
            # Provide a dummy JSON payload
            client_data = {
                "id": "mock_cred_id",
                "rawId": "mock_raw_id",
                "response": {
                    "clientDataJSON": "mock_client_data",
                    "authenticatorData": "mock_authenticator_data",
                    "signature": "mock_signature"
                },
                "type": "public-key"
            }

            response = self.client.post(
                self.complete_webauthn_auth_url, 
                data=json.dumps(client_data), 
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('WebAuthn login successful.', str(response.content))
            self.assertIn('token', response.json())
            
            cred.refresh_from_db()
            self.assertEqual(cred.sign_count, 2)
            
            # Verify session data has been cleared
            self.assertIsNone(self.client.session.get('challenge'))

    def test_delete_webauthn_credential_success(self):
        """
        Test successful deletion of a WebAuthn credential.
        """
        cred = WebAuthnCredential.objects.create(
            user=self.user,
            credential_id="to_be_deleted",
            public_key="some_key",
            sign_count=1
        )
        response = self.client.delete(reverse(self.delete_webauthn_url_name, kwargs={'pk': cred.pk}))
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WebAuthnCredential.objects.count(), 0)

    def test_delete_webauthn_credential_not_found(self):
        """
        Test deletion of a non-existent credential.
        """
        response = self.client.delete(reverse(self.delete_webauthn_url_name, kwargs={'pk': 999}))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Credential not found', str(response.content))

    def test_list_webauthn_credentials_success(self):
        """
        Test successful listing of WebAuthn credentials.
        """
        WebAuthnCredential.objects.create(user=self.user, credential_id="cred1", public_key="key1", sign_count=1)
        WebAuthnCredential.objects.create(user=self.user, credential_id="cred2", public_key="key2", sign_count=1)
        
        response = self.client.get(self.list_webauthn_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['credentials']), 2)

    def test_delete_account_success(self):
        """
        Test successful user account deletion.
        """
        response = self.client.delete(self.delete_account_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_delete_account_unauthenticated(self):
        """
        Test account deletion fails for an unauthenticated user.
        """
        self.client.credentials()
        response = self.client.delete(self.delete_account_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Authentication credentials were not provided.', str(response.content))
