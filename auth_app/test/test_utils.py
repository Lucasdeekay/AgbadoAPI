# auth_app/test_utils.py
import string
from unittest.mock import patch, mock_open, MagicMock
from django.test import TestCase
from django.core import mail
from django.utils import timezone
from django.db.utils import IntegrityError
from datetime import timedelta

import requests

# Import the functions to be tested and the models they interact with
from auth_app.utils import (
    generate_unique_referral_code,
    generate_otp,
    create_otp,
    send_otp_email,
    format_phone_number,
    send_otp_sms,
    write_to_file,
    log_to_server,
    upload_to_cloudinary,
)
from auth_app.models import User, OTP

class UtilityFunctionTests(TestCase):
    """
    Tests for utility functions in auth_app/utils.py.
    """
    def setUp(self):
        # Create a user instance to be used in tests
        self.user = User.objects.create_user(
            email='testuser@example.com',
            phone_number='2348012345678',
            state='Lagos'
        )
        self.user_with_phone = User.objects.create_user(
            email='testuser2@example.com',
            phone_number='2349012345678',
            state='Ogun'
        )

    def test_generate_unique_referral_code_uniqueness(self):
        """
        Test that a unique referral code is generated even if one already exists.
        """
        # Create a user with a specific referral code
        existing_code = 'ABCDEFGH'
        User.objects.create_user(
            email='existing@example.com',
            phone_number='2341111111111',
            state='Oyo',
            referral_code=existing_code
        )

        # The function should generate a different code
        new_code = generate_unique_referral_code()
        self.assertNotEqual(new_code, existing_code)
        self.assertEqual(len(new_code), 8)
        self.assertTrue(all(c in string.ascii_uppercase + string.digits for c in new_code))

    def test_generate_otp(self):
        """
        Test that generate_otp returns a 5-digit string of numbers.
        """
        otp = generate_otp()
        self.assertEqual(len(otp), 5)
        self.assertTrue(otp.isdigit())

    def test_create_otp(self):
        """
        Test that create_otp creates an OTP object in the database.
        """
        # Ensure OTP count is initially zero
        self.assertEqual(OTP.objects.count(), 0)
        
        # Create an OTP and check if a new object was created
        otp_instance = create_otp(self.user)
        self.assertEqual(OTP.objects.count(), 1)
        self.assertEqual(otp_instance.user, self.user)
        self.assertEqual(len(otp_instance.otp), 5)
        self.assertGreater(otp_instance.expires_at, timezone.now())

    def test_send_otp_email(self):
        """
        Test that send_otp_email correctly sends an email.
        """
        # Clear the outbox before the test
        mail.outbox = []
        
        # Call the function and check the email content
        send_otp_email(self.user, '12345')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Your OTP for password reset')
        self.assertEqual(email.body, 'Your OTP to reset your password is: 12345')
        self.assertEqual(email.to, ['testuser@example.com'])

class PhoneNumberTests(TestCase):
    """
    Tests for the format_phone_number utility function.
    """
    def test_format_phone_number_from_zero(self):
        """
        Test a number starting with 0 is formatted to E.164.
        """
        formatted_number = format_phone_number('08012345678')
        self.assertEqual(formatted_number, '2348012345678')

    def test_format_phone_number_from_plus_two_three_four(self):
        """
        Test a number starting with +234 is formatted correctly.
        """
        formatted_number = format_phone_number('+2348012345678')
        self.assertEqual(formatted_number, '2348012345678')

    def test_format_phone_number_from_two_three_four(self):
        """
        Test a number already in E.164 format remains unchanged.
        """
        formatted_number = format_phone_number('2348012345678')
        self.assertEqual(formatted_number, '2348012345678')
    
    def test_format_phone_number_with_non_digits(self):
        """
        Test a number with spaces and dashes is formatted correctly.
        """
        formatted_number = format_phone_number('  +234 (80) 123-456-78 ')
        self.assertEqual(formatted_number, '2348012345678')

@patch('auth_app.utils.requests.post')
@patch('auth_app.utils.config')
class TermiiAPITests(TestCase):
    """
    Tests for the Termii API functions.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            phone_number='2348012345678',
            state='Lagos'
        )

    def test_send_otp_sms_success(self, mock_config, mock_post):
        """
        Test a successful SMS delivery response.
        """
        # Mock the API key and a successful response from requests.post
        mock_config.return_value = 'mock_api_key'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "ok", "message": "SMS sent successfully"}
        mock_post.return_value = mock_response

        response_data = send_otp_sms(self.user, '54321')
        self.assertEqual(response_data, {"code": "ok", "message": "SMS sent successfully"})
        
        # Verify that the post call was made with the correct data
        expected_payload = {
            'to': '2348012345678',
            'from': 'Agba do',
            'sms': 'Your OTP to reset your password is: 54321',
            'type': 'plain',
            'channel': 'generic',
            'api_key': 'mock_api_key'
        }
        mock_post.assert_called_once_with(
            "https://v3.api.termii.com/api/sms/send",
            headers={"Content-Type": "application/json"},
            json=expected_payload
        )

    def test_send_otp_sms_api_failure(self, mock_config, mock_post):
        """
        Test that an exception is handled for a failed API call.
        """
        mock_config.return_value = 'mock_api_key'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_post.return_value = mock_response
        
        response_data = send_otp_sms(self.user, '54321')
        self.assertIsNone(response_data)

    def test_send_otp_sms_no_api_key(self, mock_config, mock_post):
        """
        Test that the function returns None when the API key is not configured.
        """
        mock_config.return_value = None  # Mock a missing API key
        response_data = send_otp_sms(self.user, '54321')
        self.assertIsNone(response_data)
        mock_post.assert_not_called()

@patch('auth_app.utils.open', new_callable=mock_open)
class FileLoggingTests(TestCase):
    """
    Tests for file logging functions.
    """
    def test_write_to_file(self, mock_file):
        """
        Test that write_to_file correctly writes to a file.
        """
        write_to_file("Test message", "Test error")
        
        mock_file.assert_called_once_with("file.txt", "a")
        handle = mock_file()
        handle.write.assert_any_call("Message: Test message\n")
        handle.write.assert_any_call("Error: Test error\n")

    @patch('auth_app.utils.os.makedirs')
    @patch('auth_app.utils.os.path.exists', return_value=False)
    def test_log_to_server(self, mock_exists, mock_makedirs, mock_file):
        """
        Test that log_to_server correctly logs a message with a timestamp.
        """
        log_to_server("Server log message")
        
        mock_file.assert_called_once_with("agbado.log", "a")
        handle = mock_file()
        # Check that the write call includes the timestamp and message
        write_args = [call[0][0] for call in handle.write.call_args_list]
        self.assertTrue("MESSAGE: Server log message" in write_args[0])

@patch('auth_app.utils.requests.post')
@patch('auth_app.utils.config')
class CloudinaryTests(TestCase):
    """
    Tests for Cloudinary upload function.
    """
    def test_upload_to_cloudinary_success(self, mock_config, mock_post):
        """
        Test that a successful upload returns the secure URL.
        """
        mock_config.side_effect = ['mock_cloud_name', 'mock_api_key', 'mock_upload_preset']
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"secure_url": "http://mock.url/image.jpg"}
        mock_post.return_value = mock_response

        # Use a dummy file-like object for the test
        mock_file = MagicMock()
        mock_file.seek.return_value = None # mock the seek method
        
        secure_url = upload_to_cloudinary(mock_file)
        self.assertEqual(secure_url, "http://mock.url/image.jpg")
        
        # Verify the post call was made with the correct data
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('files', kwargs)
        self.assertIn('data', kwargs)
        self.assertEqual(kwargs['data']['upload_preset'], 'mock_upload_preset')

    def test_upload_to_cloudinary_failure(self, mock_config, mock_post):
        """
        Test that a failed upload raises an exception.
        """
        mock_config.side_effect = ['mock_cloud_name', 'mock_api_key', 'mock_upload_preset']
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Upload failed"
        mock_post.return_value = mock_response

        with self.assertRaisesMessage(Exception, "Cloudinary upload failed: Upload failed"):
            upload_to_cloudinary(MagicMock())
