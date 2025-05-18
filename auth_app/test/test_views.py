from datetime import timedelta
from unittest.mock import patch

import jwt
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from auth_app.models import User as CustomUser, OTP
from rest_framework.authtoken.models import Token


# class RegisterViewTestCase(APITestCase):
#     """
#     Test cases for the RegisterView API endpoint.
#     """
#
#     def setUp(self):
#         """
#         Set up test data for all test cases.
#         """
#         self.client = APIClient()
#         self.register_url = reverse('register')  # Replace with the actual URL name for registration
#
#         # Create a user and generate a token for authentication
#         self.user = CustomUser.objects.create_user(
#             email="testuser@example.com",
#             password="password123",
#         )
#         self.user.is_email_verified = False
#         self.user.save()
#
#         # Generate token for the created user
#         self.token = Token.objects.create(user=self.user)
#
#         return super().setUp()
#
#     def tearDown(self):
#         """
#         Clean up after tests are executed.
#         """
#         CustomUser.objects.all().delete()
#         OTP.objects.all().delete()
#         return super().tearDown()
#
#     def test_successful_registration(self):
#         """
#         Test that a valid registration request creates a user, related objects, and sends an OTP.
#         """
#         data = {
#             "email": "newuser@example.com",
#             "phone_number": "1234567890",
#             "password": "password123",
#         }
#
#         # Authenticate with the token
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#
#         response = self.client.post(self.register_url, data, format='json')
#
#         # Verify response status
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertIn("token", response.data)
#         self.assertIn("user", response.data)
#
#         # Verify the user was created
#         user = CustomUser.objects.filter(email=data['email']).first()
#         self.assertIsNotNone(user)
#         self.assertFalse(user.is_active)  # User should be inactive until email verification
#         self.assertTrue(user.check_password(data['password']))
#
#         # Verify OTP generation
#         self.assertTrue(OTP.objects.filter(user=user).exists())
#
#     def test_registration_with_missing_fields(self):
#         """
#         Test that registration with missing required fields returns a 400 error.
#         """
#         # Missing email
#         data = {
#             "phone_number": "1234567890",
#             "password": "password123"
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("Email", response.data['error'])
#
#         # Missing phone number
#         data = {
#             "email": "newuser@example.com",
#             "password": "password123"
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("phone number", response.data['error'])
#
#         # Missing password
#         data = {
#             "email": "newuser@example.com",
#             "phone_number": "1234567890"
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("password", response.data['error'])
#
#     def test_registration_with_existing_email(self):
#         """
#         Test that registration with an already existing email returns a 400 error.
#         """
#         # Create a user with the same email
#         CustomUser.objects.create_user(email="existinguser@example.com", phone_number="0987654321",
#                                        password="password123")
#
#         data = {
#             "email": "existinguser@example.com",
#             "phone_number": "1234567890",
#             "password": "password123",
#         }
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "A user with this email already exists.")
#
#     def test_registration_with_existing_phone_number(self):
#         """
#         Test that registration with an already existing phone number returns a 400 error.
#         """
#         # Create a user with the same phone number
#         CustomUser.objects.create_user(email="anotheruser@example.com", phone_number="1234567890",
#                                        password="password123")
#
#         data = {
#             "email": "newuser@example.com",
#             "phone_number": "1234567890",
#             "password": "password123",
#         }
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "A user with this phone number already exists.")
#
#     def test_registration_with_invalid_email(self):
#         """
#         Test that registration with an invalid email format returns a 400 error.
#         """
#         data = {
#             "email": "invalidemail",  # Invalid email format
#             "phone_number": "1234567890",
#             "password": "password123",
#         }
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
#         response = self.client.post(self.register_url, data, format='json')
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("email", response.data)


class VerifyOTPViewTestCase(APITestCase):
    """
    Test cases for the VerifyOTPView API endpoint.
    """

    def setUp(self):
        """
        Set up test data for all test cases.
        """
        self.client = APIClient()
        self.verify_otp_url = reverse('verify-otp')  # Ensure this matches your URL name for OTP verification

        # Create a user and generate a token for authentication
        self.user = CustomUser.objects.create_user(
            email="testuser@example.com",
            phone_number="1234567890",
            password="testpassword",
            is_active=False
        )
        self.user.is_email_verified = False
        self.user.save()

        # Generate token for the created user
        self.token = Token.objects.create(user=self.user)

        # Create a valid OTP for the user
        self.otp = OTP.objects.create(
            user=self.user,
            otp="123456",
            is_used=False,
            created_at=timezone.now()
        )

        return super().setUp()

    def tearDown(self):
        """
        Clean up after tests are executed.
        """
        CustomUser.objects.all().delete()
        OTP.objects.all().delete()
        Token.objects.all().delete()
        return super().tearDown()

    def test_missing_fields(self):
        """
        Test that missing fields return a 400 error.
        """
        # Missing identifier
        data = {"otp": "123456"}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # Missing OTP
        data = {"identifier": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_non_existent_user(self):
        """
        Test that a non-existent user returns a 400 error.
        """
        # Use an identifier that does not exist
        data = {"identifier": "nonexistent@example.com", "otp": "123456"}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "User with the provided email or phone number does not exist.")

    def test_invalid_otp(self):
        """
        Test that an invalid OTP returns a 400 error.
        """
        # Use an incorrect OTP
        data = {"identifier": self.user.email, "otp": "000000"}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid OTP.")

    def test_expired_otp(self):
        """
        Test that an expired OTP returns a 400 error.
        """
        # Set OTP to expired
        self.otp.created_at = timezone.now() - timedelta(minutes=6)  # Assuming OTP expiry is 5 minutes
        self.otp.save()

        data = {"identifier": self.user.email, "otp": "123456"}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "OTP has expired.")

    def test_successful_verification(self):
        """
        Test that successful OTP verification activates the user's account.
        """
        data = {"identifier": self.user.email, "otp": "123456"}
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.verify_otp_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Account verified successfully. You can now log in.")

        # Check that the user is now verified and active
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)

        # Check that the OTP is marked as used
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.is_used)



# class LoginViewTestCase(APITestCase):
#     def setUp(self):
#         self.login_url = reverse('login')  # Make sure the URL name matches
#         self.email_user = CustomUser.objects.create_user(
#             email="emailuser@example.com",
#             phone_number="1234567890",
#             password="emailpassword",
#             is_active=True
#         )
#         self.phone_user = CustomUser.objects.create_user(
#             email="phoneuser@example.com",
#             phone_number="0987654321",
#             password="phonepassword",
#             is_active=True
#         )
#
#     def test_login_missing_fields(self):
#         # Test missing identifier
#         data = {"password": "testpassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#
#         # Test missing password
#         data = {"identifier": self.email_user.email}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#
#     def test_invalid_credentials(self):
#         # Test invalid email and password
#         data = {"identifier": "wrongemail@example.com", "password": "wrongpassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Invalid credentials.")
#
#         # Test correct email with wrong password
#         data = {"identifier": self.email_user.email, "password": "wrongpassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Invalid credentials.")
#
#     def test_login_with_email(self):
#         # Test login with valid email and password
#         data = {"identifier": self.email_user.email, "password": "emailpassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#         self.assertIn("user", response.data)
#         self.assertEqual(response.data["user"]["email"], self.email_user.email)
#
#         # Check token creation
#         token = Token.objects.get(user=self.email_user)
#         self.assertEqual(response.data["token"], token.key)
#
#     def test_login_with_phone_number(self):
#         # Test login with valid phone number and password
#         data = {"identifier": self.phone_user.phone_number, "password": "phonepassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#         self.assertIn("user", response.data)
#         self.assertEqual(response.data["user"]["phone_number"], self.phone_user.phone_number)
#
#         # Check token creation
#         token = Token.objects.get(user=self.phone_user)
#         self.assertEqual(response.data["token"], token.key)
#
#     def test_login_with_unregistered_email_or_phone(self):
#         # Test with an unregistered email
#         data = {"identifier": "notregistered@example.com", "password": "somepassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Invalid credentials.")
#
#         # Test with an unregistered phone number
#         data = {"identifier": "0000000000", "password": "somepassword"}
#         response = self.client.post(self.login_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Invalid credentials.")
#
#
# class LogoutViewTestCase(APITestCase):
#     def setUp(self):
#         self.logout_url = reverse('logout')  # Ensure this matches your URL name
#         self.user = CustomUser.objects.create_user(
#             email="testuser@example.com",
#             phone_number="1234567890",
#             password="testpassword",
#             is_active=True
#         )
#         # Create a token for the user
#         self.token = Token.objects.create(user=self.user)
#         self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
#
#     def test_unauthorized_access(self):
#         # Remove the authorization header to simulate an unauthorized request
#         self.client.credentials()  # This clears any existing credentials
#         response = self.client.post(self.logout_url)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertIn("detail", response.data)
#         self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")
#
#     def test_successful_logout(self):
#         # Test successful logout and token deletion
#         response = self.client.post(self.logout_url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("message", response.data)
#         self.assertEqual(response.data["message"], "Logged out successfully.")
#
#         # Check that the token has been deleted
#         with self.assertRaises(Token.DoesNotExist):
#             Token.objects.get(user=self.user)
#
#
# class ForgotPasswordViewTestCase(APITestCase):
#     def setUp(self):
#         self.forgot_password_url = reverse('forgot-password')  # Make sure the URL name matches
#         self.email_user = CustomUser.objects.create_user(
#             email="emailuser@example.com",
#             phone_number="1234567890",
#             password="testpassword",
#             is_active=True
#         )
#         self.phone_user = CustomUser.objects.create_user(
#             email="phoneuser@example.com",
#             phone_number="0987654321",
#             password="testpassword",
#             is_active=True
#         )
#
#     def test_missing_identifier(self):
#         # Test missing identifier field
#         data = {}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Email or Phone number is required.")
#
#     def test_unregistered_identifier(self):
#         # Test with an unregistered email
#         data = {"identifier": "notregistered@example.com"}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "User with the provided email or phone number does not exist.")
#
#         # Test with an unregistered phone number
#         data = {"identifier": "0000000000"}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "User with the provided email or phone number does not exist.")
#
#     @patch('auth_app.utils.create_otp')
#     def test_otp_already_sent(self, mock_create_otp):
#         # Simulate an OTP that is still valid
#         OTP.objects.create(user=self.email_user, otp="123456", is_used=False)
#
#         data = {"identifier": self.email_user.email}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "An OTP was already sent. Please check your email/phone.")
#
#         # Test with phone number for the same case
#         OTP.objects.create(user=self.phone_user, otp="654321", is_used=False)
#
#         data = {"identifier": self.phone_user.phone_number}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "An OTP was already sent. Please check your email/phone.")
#
#     @patch('auth_app.utils.send_otp_email')
#     @patch('auth_app.utils.send_otp_sms')
#     @patch('auth_app.utils.create_otp')
#     def test_successful_otp_generation(self, mock_create_otp, mock_send_otp_email, mock_send_otp_sms):
#         # Mock the OTP creation and sending methods
#         mock_create_otp.return_value.otp = "111111"
#         mock_send_otp_email.return_value = None
#         mock_send_otp_sms.return_value = None
#
#         # Test successful OTP generation for email
#         data = {"identifier": self.email_user.email}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("message", response.data)
#         self.assertEqual(response.data["message"], "OTP sent to your email and phone number.")
#
#         # Test successful OTP generation for phone number
#         data = {"identifier": self.phone_user.phone_number}
#         response = self.client.post(self.forgot_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("message", response.data)
#         self.assertEqual(response.data["message"], "OTP sent to your email and phone number.")
#
#
#
# class RetrievePasswordViewTestCase(APITestCase):
#     def setUp(self):
#         self.retrieve_password_url = reverse('retrieve-password')  # Make sure this matches your URL name
#         self.user = CustomUser.objects.create_user(
#             email="testuser@example.com",
#             phone_number="1234567890",
#             password="oldpassword",
#             is_active=True
#         )
#
#     def test_missing_required_fields(self):
#         # Test when no data is provided
#         data = {}
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(
#             response.data["error"],
#             "Identifier (email or phone), OTP, and new password are required."
#         )
#
#         # Test when only some fields are provided
#         data = {"identifier": "testuser@example.com"}
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = {"identifier": "testuser@example.com", "otp": "123456"}
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#     def test_unregistered_identifier(self):
#         # Test with an unregistered email
#         data = {
#             "identifier": "unknown@example.com",
#             "otp": "123456",
#             "new_password": "newpassword123"
#         }
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(
#             response.data["error"],
#             "User with the provided email or phone number does not exist."
#         )
#
#     def test_invalid_otp(self):
#         # Test with an invalid OTP
#         data = {
#             "identifier": self.user.email,
#             "otp": "invalid_otp",
#             "new_password": "newpassword123"
#         }
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["error"], "Invalid OTP.")
#
#     def test_expired_otp(self):
#         # Create an expired OTP
#         expired_otp = OTP.objects.create(user=self.user, otp="123456", is_used=False)
#         with patch.object(expired_otp, 'is_expired', return_value=True):
#             data = {
#                 "identifier": self.user.email,
#                 "otp": expired_otp.otp,
#                 "new_password": "newpassword123"
#             }
#             response = self.client.post(self.retrieve_password_url, data)
#             self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#             self.assertEqual(response.data["error"], "OTP has expired.")
#
#     def test_successful_password_reset(self):
#         # Create a valid OTP
#         otp_instance = OTP.objects.create(user=self.user, otp="123456", is_used=False)
#
#         data = {
#             "identifier": self.user.email,
#             "otp": otp_instance.otp,
#             "new_password": "newpassword123"
#         }
#         response = self.client.post(self.retrieve_password_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["message"], "Password has been successfully reset.")
#
#         # Verify the password has been changed
#         self.user.refresh_from_db()
#         self.assertTrue(self.user.check_password("newpassword123"))
#
#         # Verify the OTP is marked as used
#         otp_instance.refresh_from_db()
#         self.assertTrue(otp_instance.is_used)
#
#
# class GoogleAuthViewTestCase(APITestCase):
#     def setUp(self):
#         self.google_auth_url = reverse('google-auth')  # Make sure this matches your URL name
#
#     def test_missing_token(self):
#         # Test when no token is provided
#         data = {}
#         response = self.client.post(self.google_auth_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Token is required")
#
#     @patch('auth_app.utils.get_google_user_info')  # Replace with the actual import path of your get_google_user_info function
#     def test_invalid_token(self, mock_get_google_user_info):
#         # Mock the behavior of get_google_user_info to raise an Exception for invalid token
#         mock_get_google_user_info.side_effect = Exception("Invalid token")
#
#         data = {"token": "invalid_token"}
#         response = self.client.post(self.google_auth_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["error"], "Invalid token")
#
#     @patch('auth_app.utils.get_google_user_info')
#     def test_successful_user_creation(self, mock_get_google_user_info):
#         # Mock the response from get_google_user_info
#         mock_get_google_user_info.return_value = {
#             "email": "newuser@example.com",
#             "given_name": "John",
#             "family_name": "Doe"
#         }
#
#         data = {"token": "valid_token"}
#         response = self.client.post(self.google_auth_url, data)
#
#         # Check if the user was created successfully
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#
#         # Verify user details
#         user = CustomUser.objects.get(email="newuser@example.com")
#         self.assertEqual(user.first_name, "John")
#         self.assertEqual(user.last_name, "Doe")
#         self.assertTrue(user.is_verified)
#
#         # Verify that the token belongs to the created user
#         token = Token.objects.get(user=user)
#         self.assertEqual(response.data["token"], token.key)
#
#     @patch('auth_app.utils.get_google_user_info')
#     def test_successful_user_retrieval(self, mock_get_google_user_info):
#         # Create an existing user
#         user = CustomUser.objects.create_user(
#             email="existinguser@example.com",
#             password="testpassword",
#             is_verified=False
#         )
#
#         # Mock the response from get_google_user_info
#         mock_get_google_user_info.return_value = {
#             "email": "existinguser@example.com",
#             "given_name": "Alice",
#             "family_name": "Smith"
#         }
#
#         data = {"token": "valid_token"}
#         response = self.client.post(self.google_auth_url, data)
#
#         # Check if the user details were updated and verified
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#
#         # Verify user details update
#         user.refresh_from_db()
#         self.assertEqual(user.first_name, "Alice")
#         self.assertEqual(user.last_name, "Smith")
#         self.assertTrue(user.is_verified)
#
#         # Verify that the token belongs to the existing user
#         token = Token.objects.get(user=user)
#         self.assertEqual(response.data["token"], token.key)
#
#
# class AppleAuthViewTestCase(APITestCase):
#     def setUp(self):
#         self.apple_auth_url = reverse('apple-auth')  # Ensure this matches your URL name
#
#     def test_missing_code(self):
#         # Test when no authorization code is provided
#         data = {}
#         response = self.client.post(self.apple_auth_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.data)
#         self.assertEqual(response.data["error"], "Authorization code is required")
#
#     @patch('auth_app.utils.get_apple_user_info')  # Replace with the actual import path of your get_apple_user_info function
#     def test_invalid_token(self, mock_get_apple_user_info):
#         # Mock the behavior of get_apple_user_info to raise an exception for invalid token
#         mock_get_apple_user_info.side_effect = Exception("Invalid Apple ID token")
#
#         data = {"code": "invalid_code"}
#         response = self.client.post(self.apple_auth_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["error"], "Invalid Apple ID token")
#
#     @patch('auth_app.utils.get_apple_user_info')
#     def test_token_without_email(self, mock_get_apple_user_info):
#         # Mock the response from get_apple_user_info where the token does not contain an email
#         mock_get_apple_user_info.return_value = "invalid_token_without_email"
#
#         # Simulate decoding of a token without email
#         invalid_decoded_token = {
#             "sub": "user_id",  # No email in this token
#         }
#         mock_get_apple_user_info.return_value = jwt.encode(invalid_decoded_token, 'secret', algorithm='HS256')
#
#         data = {"code": "valid_code"}
#         response = self.client.post(self.apple_auth_url, data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data["error"], "Apple ID token did not contain email")
#
#     @patch('auth_app.utils.get_apple_user_info')
#     def test_successful_user_creation(self, mock_get_apple_user_info):
#         # Mock the response from get_apple_user_info with valid data
#         mock_get_apple_user_info.return_value = "valid_token_with_email"
#         valid_decoded_token = {
#             "email": "newuser@example.com",
#             "sub": "user_id",
#         }
#         mock_get_apple_user_info.return_value = jwt.encode(valid_decoded_token, 'secret', algorithm='HS256')
#
#         data = {"code": "valid_code"}
#         response = self.client.post(self.apple_auth_url, data)
#
#         # Check if the user was created successfully
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#
#         # Verify user details
#         user = CustomUser.objects.get(email="newuser@example.com")
#         self.assertTrue(user.is_verified)
#
#         # Verify that the token belongs to the created user
#         token = Token.objects.get(user=user)
#         self.assertEqual(response.data["token"], token.key)
#
#     @patch('auth_app.utils.get_apple_user_info')
#     def test_successful_user_retrieval(self, mock_get_apple_user_info):
#         # Create an existing user
#         user = CustomUser.objects.create_user(
#             email="existinguser@example.com",
#             password="testpassword",
#             is_verified=False
#         )
#
#         # Mock the response from get_apple_user_info
#         valid_decoded_token = {
#             "email": "existinguser@example.com",
#             "sub": "user_id",
#         }
#         mock_get_apple_user_info.return_value = jwt.encode(valid_decoded_token, 'secret', algorithm='HS256')
#
#         data = {"code": "valid_code"}
#         response = self.client.post(self.apple_auth_url, data)
#
#         # Check if the user details were updated and verified
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("token", response.data)
#
#         # Verify user details update
#         user.refresh_from_db()
#         self.assertTrue(user.is_verified)
#
#         # Verify that the token belongs to the existing user
#         token = Token.objects.get(user=user)
#         self.assertEqual(response.data["token"], token.key)
