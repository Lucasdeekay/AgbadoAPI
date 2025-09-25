# authentication/test_signals.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

class SignalTests(TestCase):
    """
    Tests for the Django signals in the authentication app.
    """

    def setUp(self):
        self.user_model = get_user_model()

    @patch('auth_app.signals.create_dedicated_account_for_user')
    def test_create_dedicated_account_on_signup_signal_fires(self, mock_create_account):
        """
        Test that the signal to create a dedicated account is triggered on user creation.
        """
        # Create a new user, which should trigger the post_save signal
        new_user = self.user_model.objects.create_user(
            email='newuser@example.com',
            password='testpassword',
            phone_number='2341234567890',
            state='Lagos'
        )
        
        # Assert that the mocked function was called
        mock_create_account.assert_called_once()
        
        # Assert that the function was called with the correct user instance
        mock_create_account.assert_called_with(new_user)

    @patch('auth_app.signals.create_dedicated_account_for_user')
    def test_signal_does_not_fire_on_update(self, mock_create_account):
        """
        Test that the signal does not fire when an existing user is updated.
        """
        # First, create a user and clear the mock's call count
        existing_user = self.user_model.objects.create_user(
            email='existinguser@example.com',
            password='testpassword',
            phone_number='2341234567891',
            state='Ogun'
        )
        mock_create_account.reset_mock()
        
        # Update the user's details without creating a new instance
        existing_user.first_name = 'UpdatedName'
        existing_user.save()
        
        # Assert that the mocked function was NOT called
        mock_create_account.assert_not_called()

    @patch('auth_app.signals.create_dedicated_account_for_user')
    def test_signal_handles_exception_gracefully(self, mock_create_account):
        """
        Test that the signal handles exceptions from the service function without crashing.
        """
        # Configure the mocked function to raise an exception
        mock_create_account.side_effect = Exception('Monnify service is down')
        
        # Create a new user. The signal's try/except block should prevent any
        # exception from being raised here.
        self.user_model.objects.create_user(
            email='erroruser@example.com',
            password='testpassword',
            phone_number='2341234567892',
            state='Abuja'
        )
        
        # Assert that the user was created successfully
        self.assertTrue(self.user_model.objects.filter(email='erroruser@example.com').exists())

        # Assert that the mocked function was still called once,
        # showing that the signal attempted to execute the code.
        mock_create_account.assert_called_once()
