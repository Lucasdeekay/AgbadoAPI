"""
Tests for provider_app models, serializers, and views.

This module contains comprehensive tests for service provider-related functionality
including business information, approval processes, and rating management.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal

from .models import ServiceProvider
from .serializers import (
    ServiceProviderSerializer, ServiceProviderListSerializer, ServiceProviderDetailSerializer
)

User = get_user_model()


class ServiceProviderModelTest(TestCase):
    """Test cases for ServiceProvider model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street, Test City",
            company_description="A test company for testing purposes",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical",
            opening_hour="08:00",
            closing_hour="18:00"
        )

    def test_service_provider_creation(self):
        """Test that a service provider can be created."""
        self.assertEqual(self.service_provider.user, self.user)
        self.assertEqual(self.service_provider.company_name, "Test Company")
        self.assertEqual(self.service_provider.business_category, "Electrical")
        self.assertFalse(self.service_provider.is_approved)
        self.assertEqual(self.service_provider.avg_rating, Decimal('0.00'))

    def test_service_provider_string_representation(self):
        """Test the string representation of a service provider."""
        self.assertEqual(str(self.service_provider), "Test Company")

    def test_get_business_hours(self):
        """Test getting formatted business hours."""
        hours = self.service_provider.get_business_hours()
        self.assertEqual(hours, "08:00 - 18:00")

    def test_get_business_hours_partial(self):
        """Test getting business hours with partial information."""
        # Test with only opening hour
        self.service_provider.closing_hour = None
        self.service_provider.save()
        hours = self.service_provider.get_business_hours()
        self.assertEqual(hours, "Opens at 08:00")

        # Test with only closing hour
        self.service_provider.opening_hour = None
        self.service_provider.closing_hour = "18:00"
        self.service_provider.save()
        hours = self.service_provider.get_business_hours()
        self.assertEqual(hours, "Closes at 18:00")

        # Test with no hours
        self.service_provider.closing_hour = None
        self.service_provider.save()
        hours = self.service_provider.get_business_hours()
        self.assertEqual(hours, "Hours not specified")

    def test_update_rating(self):
        """Test updating average rating."""
        # Add first rating
        self.service_provider.update_rating(4)
        self.assertEqual(self.service_provider.avg_rating, Decimal('4.00'))
        self.assertEqual(self.service_provider.rating_population, 1)

        # Add second rating
        self.service_provider.update_rating(5)
        self.assertEqual(self.service_provider.avg_rating, Decimal('4.50'))
        self.assertEqual(self.service_provider.rating_population, 2)

    def test_update_rating_invalid(self):
        """Test updating rating with invalid values."""
        initial_rating = self.service_provider.avg_rating
        initial_population = self.service_provider.rating_population

        # Test with invalid rating
        self.service_provider.update_rating(6)  # Invalid
        self.assertEqual(self.service_provider.avg_rating, initial_rating)
        self.assertEqual(self.service_provider.rating_population, initial_population)

        self.service_provider.update_rating(0)  # Invalid
        self.assertEqual(self.service_provider.avg_rating, initial_rating)
        self.assertEqual(self.service_provider.rating_population, initial_population)

    def test_is_open_now(self):
        """Test checking if business is currently open."""
        # This test depends on current time, so we'll test the logic
        # by temporarily setting hours that should be open
        self.service_provider.opening_hour = "00:00"
        self.service_provider.closing_hour = "23:59"
        self.service_provider.save()
        
        # Should be open with these hours
        self.assertTrue(self.service_provider.is_open_now())

        # Test with no hours
        self.service_provider.opening_hour = None
        self.service_provider.closing_hour = None
        self.service_provider.save()
        self.assertFalse(self.service_provider.is_open_now())

    def test_get_approved_providers(self):
        """Test getting approved service providers."""
        # Create another provider
        user2 = User.objects.create_user(
            email="provider2@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        provider2 = ServiceProvider.objects.create(
            user=user2,
            company_name="Approved Company",
            company_address="456 Test Street",
            company_phone_no="0987654321",
            company_email="approved@test.com",
            business_category="Plumbing",
            is_approved=True
        )

        approved_providers = ServiceProvider.get_approved_providers()
        self.assertEqual(approved_providers.count(), 1)
        self.assertEqual(approved_providers.first(), provider2)

    def test_get_providers_by_category(self):
        """Test getting service providers by category."""
        # Create another provider in same category
        user2 = User.objects.create_user(
            email="provider2@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        provider2 = ServiceProvider.objects.create(
            user=user2,
            company_name="Another Electrical Company",
            company_address="456 Test Street",
            company_phone_no="0987654321",
            company_email="another@test.com",
            business_category="Electrical",
            is_approved=True
        )

        electrical_providers = ServiceProvider.get_providers_by_category("Electrical")
        self.assertEqual(electrical_providers.count(), 1)
        self.assertEqual(electrical_providers.first(), provider2)

    def test_one_to_one_relationship(self):
        """Test that a user can only have one service provider profile."""
        with self.assertRaises(Exception):
            ServiceProvider.objects.create(
                user=self.user,
                company_name="Duplicate Company",
                company_address="789 Test Street",
                company_phone_no="1111111111",
                company_email="duplicate@test.com",
                business_category="Plumbing"
            )


class ServiceProviderSerializerTest(TestCase):
    """Test cases for ServiceProviderSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical"
        )
        self.serializer = ServiceProviderSerializer(instance=self.service_provider)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'company_name', 'company_address', 'company_description',
            'company_phone_no', 'company_email', 'business_category', 'company_logo',
            'opening_hour', 'closing_hour', 'avg_rating', 'rating_population',
            'is_approved', 'created_at'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_company_name_field_content(self):
        """Test the company name field content."""
        data = self.serializer.data
        self.assertEqual(data['company_name'], self.service_provider.company_name)

    def test_validate_company_name_empty(self):
        """Test company name validation with empty name."""
        serializer = ServiceProviderSerializer()
        with self.assertRaises(Exception):
            serializer.validate_company_name("")

    def test_validate_company_name_too_long(self):
        """Test company name validation with too long name."""
        serializer = ServiceProviderSerializer()
        long_name = "x" * 201
        with self.assertRaises(Exception):
            serializer.validate_company_name(long_name)

    def test_validate_company_email_invalid(self):
        """Test company email validation with invalid email."""
        serializer = ServiceProviderSerializer()
        with self.assertRaises(Exception):
            serializer.validate_company_email("invalid-email")

    def test_validate_phone_number_too_short(self):
        """Test phone number validation with too short number."""
        serializer = ServiceProviderSerializer()
        with self.assertRaises(Exception):
            serializer.validate_company_phone_no("123")

    def test_validate_phone_number_too_long(self):
        """Test phone number validation with too long number."""
        serializer = ServiceProviderSerializer()
        long_phone = "1" * 16
        with self.assertRaises(Exception):
            serializer.validate_company_phone_no(long_phone)

    def test_validate_opening_hour_invalid_format(self):
        """Test opening hour validation with invalid format."""
        serializer = ServiceProviderSerializer()
        with self.assertRaises(Exception):
            serializer.validate_opening_hour("25:00")

    def test_validate_closing_hour_invalid_format(self):
        """Test closing hour validation with invalid format."""
        serializer = ServiceProviderSerializer()
        with self.assertRaises(Exception):
            serializer.validate_closing_hour("12:60")

    def test_validate_business_hours_consistency(self):
        """Test business hours consistency validation."""
        serializer = ServiceProviderSerializer()
        data = {
            'opening_hour': '18:00',
            'closing_hour': '08:00'
        }
        with self.assertRaises(Exception):
            serializer.validate(data)


class ServiceProviderListSerializerTest(TestCase):
    """Test cases for ServiceProviderListSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical"
        )
        self.serializer = ServiceProviderListSerializer(instance=self.service_provider)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'company_name', 'business_category', 'company_logo',
            'avg_rating', 'rating_population', 'is_approved', 'created_at'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_excludes_user_field(self):
        """Test that user field is excluded from list view."""
        data = self.serializer.data
        self.assertNotIn('user', data)


class ServiceProviderDetailSerializerTest(TestCase):
    """Test cases for ServiceProviderDetailSerializer."""

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
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical"
        )
        self.serializer = ServiceProviderDetailSerializer(instance=self.service_provider)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'user_email', 'user_name', 'company_name',
            'company_address', 'company_description', 'company_phone_no',
            'company_email', 'business_category', 'company_logo',
            'opening_hour', 'closing_hour', 'avg_rating', 'rating_population',
            'is_approved', 'created_at'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_user_email_field(self):
        """Test the user_email field content."""
        data = self.serializer.data
        self.assertEqual(data['user_email'], self.user.email)

    def test_user_name_field(self):
        """Test the user_name field content."""
        data = self.serializer.data
        self.assertEqual(data['user_name'], "Test User")


class ProviderAppViewsTest(APITestCase):
    """Test cases for provider app views."""

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
        
        # Create test service provider
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical"
        )

    def test_create_service_provider(self):
        """Test creating a service provider."""
        url = reverse('create_service_provider')
        data = {
            'company_name': 'New Company',
            'company_address': '456 New Street',
            'company_phone_no': '0987654321',
            'company_email': 'new@company.com',
            'business_category': 'Plumbing'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('service_provider', response.data)

    def test_edit_service_provider(self):
        """Test editing a service provider."""
        url = reverse('edit_service_provider')
        data = {
            'company_name': 'Updated Company',
            'company_address': '789 Updated Street'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'Updated Company')

    def test_get_service_provider_details(self):
        """Test getting service provider details."""
        url = reverse('get_service_provider_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('service_provider', response.data)

    def test_get_service_provider_details_unauthenticated(self):
        """Test getting service provider details without authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('get_service_provider_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProviderAppViewSetsTest(APITestCase):
    """Test cases for provider app ViewSets."""

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
        
        # Create test service provider
        self.service_provider = ServiceProvider.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="123 Test Street",
            company_phone_no="1234567890",
            company_email="company@test.com",
            business_category="Electrical"
        )

    def test_service_provider_list(self):
        """Test listing service providers."""
        url = reverse('serviceprovider-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_service_provider_detail(self):
        """Test getting service provider details."""
        url = reverse('serviceprovider-detail', args=[self.service_provider.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], self.service_provider.company_name)

    def test_service_provider_create(self):
        """Test creating a service provider."""
        url = reverse('serviceprovider-list')
        data = {
            'user': self.user.id,
            'company_name': 'New Company',
            'company_address': '456 New Street',
            'company_phone_no': '0987654321',
            'company_email': 'new@company.com',
            'business_category': 'Plumbing'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'New Company')

    def test_service_provider_update(self):
        """Test updating a service provider."""
        url = reverse('serviceprovider-detail', args=[self.service_provider.id])
        data = {'company_name': 'Updated Company'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'Updated Company')

    def test_service_provider_delete(self):
        """Test deleting a service provider."""
        url = reverse('serviceprovider-detail', args=[self.service_provider.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_service_provider_filter_by_category(self):
        """Test filtering service providers by category."""
        url = reverse('serviceprovider-list')
        response = self.client.get(url, {'business_category': 'Electrical'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_service_provider_search(self):
        """Test searching service providers."""
        url = reverse('serviceprovider-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_service_provider_ordering(self):
        """Test ordering service providers."""
        # Create another service provider
        user2 = User.objects.create_user(
            email="provider2@example.com",
            password="testpass123",
            phone_number="0987654321",
            state="Test State"
        )
        ServiceProvider.objects.create(
            user=user2,
            company_name="Another Company",
            company_address="456 Another Street",
            company_phone_no="0987654321",
            company_email="another@company.com",
            business_category="Plumbing"
        )
        
        url = reverse('serviceprovider-list')
        response = self.client.get(url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
