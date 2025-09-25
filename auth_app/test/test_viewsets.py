# authentication/test_views.py

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock
import logging

from auth_app.models import User, KYC, OTP, Referral
from auth_app.serializers import UserSerializer, KYCSerializer, OTPSerializer, ReferralSerializer

# Mocks for external dependencies to prevent side effects during testing.
@patch.object(logging.Logger, 'info', MagicMock())
class APITestCaseBase(APITestCase):
    """Base test class for all API view tests."""

    def setUp(self):
        self.user_model = get_user_model()
        self.client = APIClient()

        # Create a test user for authenticated requests
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'phone_number': '2348012345678',
            'state': 'Lagos'
        }
        self.user = self.user_model.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

        # Create a second user for testing permissions
        self.other_user = self.user_model.objects.create_user(
            email='otheruser@example.com',
            password='testpassword456',
            phone_number='2348087654321',
            state='Oyo'
        )
        
        # Define URLs
        self.user_list_url = reverse('user-list')
        self.user_detail_url = reverse('user-detail', args=[self.user.id])
        self.kyc_list_url = reverse('kyc-list')
        self.otp_list_url = reverse('otp-list')
        self.referral_list_url = reverse('referral-list')

class UserViewSetTests(APITestCaseBase):
    """Tests for the UserViewSet."""

    def test_list_users(self):
        """Test listing users is successful and paginated."""
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('results', response.data)

    def test_retrieve_user(self):
        """Test retrieving a specific user is successful."""
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        self.client.logout()
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('auth_app.serializers.upload_to_cloudinary', return_value='http://test.url/image.jpg')
    @patch('auth_app.serializers.generate_unique_referral_code', return_value='NEWCODE')
    def test_create_user(self, mock_referral_code, mock_upload):
        """Test creating a new user is successful."""
        self.client.force_authenticate(user=self.user)
        new_user_data = {
            'email': 'newtestuser@example.com',
            'password': 'newpassword123',
            'phone_number': '2349098765432',
            'state': 'Ogun'
        }
        response = self.client.post(self.user_list_url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user_model.objects.count(), 3)
        self.assertTrue(self.user_model.objects.get(email='newtestuser@example.com').is_active)
        self.assertFalse(self.user_model.objects.get(email='newtestuser@example.com').is_verified)

    def test_update_user(self):
        """Test updating a user is successful."""
        update_data = {'first_name': 'UpdatedName'}
        response = self.client.patch(self.user_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedName')

    def test_delete_user(self):
        """Test deleting a user is successful."""
        response = self.client.delete(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.user_model.objects.count(), 1)
        self.assertFalse(self.user_model.objects.filter(id=self.user.id).exists())


class KYCViewSetTests(APITestCaseBase):
    """Tests for the KYCViewSet."""

    def setUp(self):
        super().setUp()
        self.kyc = KYC.objects.create(user=self.user, bvn='12345678901')
        self.other_kyc = KYC.objects.create(user=self.other_user, bvn='11111111111')
        self.kyc_detail_url = reverse('kyc-detail', args=[self.kyc.id])

    def test_list_own_kyc(self):
        """Test that a user can only list their own KYC records."""
        response = self.client.get(self.kyc_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)

    def test_retrieve_own_kyc(self):
        """Test retrieving a specific KYC record that belongs to the user."""
        response = self.client.get(self.kyc_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)

    def test_retrieve_other_user_kyc_denied(self):
        """Test that a user cannot retrieve another user's KYC record."""
        other_kyc_detail_url = reverse('kyc-detail', args=[self.other_kyc.id])
        response = self.client.get(other_kyc_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # @patch('auth_app.serializers.update_bvn_on_reserved_account')
    # def test_create_kyc(self, mock_update_bvn):
    #     """Test creating a KYC record is successful."""
    #     data = {'user': self.user.id, 'bvn': '09876543210'}
    #     response = self.client.post(self.kyc_list_url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(KYC.objects.filter(user=self.user).count(), 2)

    # def test_update_kyc_bvn_denied(self):
    #     """Test that a user cannot update their BVN."""
    #     update_data = {'bvn': '11111111111'}
    #     response = self.client.patch(self.kyc_detail_url, update_data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OTPViewSetTests(APITestCaseBase):
    """Tests for the OTPViewSet."""
    
    def setUp(self):
        super().setUp()
        self.otp = OTP.objects.create(user=self.user, otp='123456')
        self.other_otp = OTP.objects.create(user=self.other_user, otp='654321')
        self.otp_detail_url = reverse('otp-detail', args=[self.otp.id])

    def test_list_own_otp(self):
        """Test that a user can only list their own OTP records."""
        response = self.client.get(self.otp_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)

    def test_retrieve_other_user_otp_denied(self):
        """Test that a user cannot retrieve another user's OTP record."""
        other_otp_detail_url = reverse('otp-detail', args=[self.other_otp.id])
        response = self.client.get(other_otp_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_otp(self):
        """Test creating an OTP record is successful."""
        data = {'user': self.user.id, 'otp': '999888'}
        response = self.client.post(self.otp_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OTP.objects.filter(user=self.user).count(), 2)

    def test_update_otp_status(self):
        """Test updating an OTP record is successful."""
        update_data = {'is_used': True}
        response = self.client.patch(self.otp_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.is_used)


class ReferralViewSetTests(APITestCaseBase):
    """Tests for the ReferralViewSet."""

    def setUp(self):
        super().setUp()
        self.referral = Referral.objects.create(user=self.user, referer=self.other_user)
        self.other_referral = Referral.objects.create(user=self.other_user, referer=self.user)
        self.referral_detail_url = reverse('referral-detail', args=[self.referral.id])

    def test_list_own_referrals(self):
        """Test that a user can only list their own referral records."""
        response = self.client.get(self.referral_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user']['id'], self.user.id)

    def test_retrieve_own_referral(self):
        """Test retrieving a specific referral record that belongs to the user."""
        response = self.client.get(self.referral_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['id'], self.user.id)

    def test_retrieve_other_user_referral_denied(self):
        """Test that a user cannot retrieve another user's referral record."""
        other_referral_detail_url = reverse('referral-detail', args=[self.other_referral.id])
        response = self.client.get(other_referral_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_create_referral(self):
    #     """Test creating a referral record is successful."""
    #     new_user = self.user_model.objects.create_user(
    #         email='thirduser@example.com',
    #         password='testpassword999',
    #         phone_number='2347012345678',
    #         state='Lagos'
    #     )
    #     referral_user = self.user_model.objects.create_user(
    #         email='fourthuser@example.com',
    #         password='testpassword969',
    #         phone_number='2347012345578',
    #         state='Lagos'
    #     )
    #     data = {'user': new_user.id, 'referer': referral_user.id}
    #     response = self.client.post(self.referral_list_url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(Referral.objects.filter(user=new_user).count(), 1)

