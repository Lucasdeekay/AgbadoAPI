"""
Tests for service app models, serializers, and views.

This module contains comprehensive tests for service-related functionality
including models, serializers, views, and API endpoints.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Service, SubService, ServiceRequest, ServiceRequestBid, Booking
from .serializers import (
    ServiceSerializer, SubServiceSerializer, ServiceRequestSerializer,
    ServiceRequestBidSerializer, BookingSerializer
)
from provider_app.models import ServiceProvider

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test cases for Service model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00'),
            is_active=True
        )

    def test_service_creation(self):
        """Test service creation."""
        self.assertEqual(self.service.provider, self.provider)
        self.assertEqual(self.service.name, 'Test Service')
        self.assertEqual(self.service.category, 'Technology')
        self.assertEqual(self.service.min_price, Decimal('100.00'))
        self.assertEqual(self.service.max_price, Decimal('500.00'))

    def test_service_string_representation(self):
        """Test service string representation."""
        expected = f"Test Service by {self.provider.company_name}"
        self.assertEqual(str(self.service), expected)

    def test_get_price_range_display(self):
        """Test price range display."""
        expected = "₦100.00 - ₦500.00"
        self.assertEqual(self.service.get_price_range_display(), expected)

    def test_is_available(self):
        """Test service availability."""
        self.assertTrue(self.service.is_available())
        
        self.service.is_active = False
        self.assertFalse(self.service.is_available())

    def test_get_subservices_count(self):
        """Test getting subservices count."""
        SubService.objects.create(
            service=self.service,
            name='Sub Service 1',
            description='Sub service description',
            price=Decimal('150.00')
        )
        SubService.objects.create(
            service=self.service,
            name='Sub Service 2',
            description='Sub service description 2',
            price=Decimal('200.00')
        )
        
        self.assertEqual(self.service.get_subservices_count(), 2)


class SubServiceModelTest(TestCase):
    """Test cases for SubService model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )
        self.subservice = SubService.objects.create(
            service=self.service,
            name='Test Sub Service',
            description='Test sub service description',
            price=Decimal('150.00'),
            is_active=True
        )

    def test_subservice_creation(self):
        """Test subservice creation."""
        self.assertEqual(self.subservice.service, self.service)
        self.assertEqual(self.subservice.name, 'Test Sub Service')
        self.assertEqual(self.subservice.price, Decimal('150.00'))

    def test_subservice_string_representation(self):
        """Test subservice string representation."""
        expected = f"Test Sub Service - ₦150.00"
        self.assertEqual(str(self.subservice), expected)

    def test_get_price_display(self):
        """Test formatted price display."""
        expected = "₦150.00"
        self.assertEqual(self.subservice.get_price_display(), expected)

    def test_is_available(self):
        """Test subservice availability."""
        self.assertTrue(self.subservice.is_available())
        
        self.subservice.is_active = False
        self.assertFalse(self.subservice.is_available())


class ServiceRequestModelTest(TestCase):
    """Test cases for ServiceRequest model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.service_request = ServiceRequest.objects.create(
            user=self.user,
            title='Test Request',
            description='Test request description',
            category='Technology',
            price=Decimal('200.00'),
            status='pending'
        )

    def test_service_request_creation(self):
        """Test service request creation."""
        self.assertEqual(self.service_request.user, self.user)
        self.assertEqual(self.service_request.title, 'Test Request')
        self.assertEqual(self.service_request.category, 'Technology')
        self.assertEqual(self.service_request.price, Decimal('200.00'))

    def test_service_request_string_representation(self):
        """Test service request string representation."""
        expected = f"Test Request by {self.user.email} (pending)"
        self.assertEqual(str(self.service_request), expected)

    def test_get_price_display(self):
        """Test formatted price display."""
        expected = "₦200.00"
        self.assertEqual(self.service_request.get_price_display(), expected)

    def test_is_open_for_bids(self):
        """Test if request is open for bids."""
        self.assertTrue(self.service_request.is_open_for_bids())
        
        self.service_request.status = 'awarded'
        self.assertFalse(self.service_request.is_open_for_bids())


class ServiceRequestBidModelTest(TestCase):
    """Test cases for ServiceRequestBid model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service_request = ServiceRequest.objects.create(
            user=self.user,
            title='Test Request',
            description='Test request description',
            category='Technology',
            price=Decimal('200.00')
        )
        self.bid = ServiceRequestBid.objects.create(
            service_request=self.service_request,
            provider=self.provider,
            amount=Decimal('150.00'),
            proposal='Test proposal',
            status='pending'
        )

    def test_bid_creation(self):
        """Test bid creation."""
        self.assertEqual(self.bid.service_request, self.service_request)
        self.assertEqual(self.bid.provider, self.provider)
        self.assertEqual(self.bid.amount, Decimal('150.00'))
        self.assertEqual(self.bid.status, 'pending')

    def test_bid_string_representation(self):
        """Test bid string representation."""
        expected = f"Bid by {self.provider.company_name} for {self.service_request.title} (pending)"
        self.assertEqual(str(self.bid), expected)

    def test_get_amount_display(self):
        """Test formatted amount display."""
        expected = "₦150.00"
        self.assertEqual(self.bid.get_amount_display(), expected)

    def test_is_accepted(self):
        """Test if bid is accepted."""
        self.assertFalse(self.bid.is_accepted())
        
        self.bid.status = 'accepted'
        self.assertTrue(self.bid.is_accepted())


class BookingModelTest(TestCase):
    """Test cases for Booking model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )
        self.booking = Booking.objects.create(
            user=self.user,
            service=self.service,
            booking_date='2024-01-15',
            status='confirmed'
        )

    def test_booking_creation(self):
        """Test booking creation."""
        self.assertEqual(self.booking.user, self.user)
        self.assertEqual(self.booking.service, self.service)
        self.assertEqual(self.booking.status, 'confirmed')

    def test_booking_string_representation(self):
        """Test booking string representation."""
        expected = f"Booking by {self.user.email} for {self.service.name} (confirmed)"
        self.assertEqual(str(self.booking), expected)

    def test_is_confirmed(self):
        """Test if booking is confirmed."""
        self.assertTrue(self.booking.is_confirmed())
        
        self.booking.status = 'pending'
        self.assertFalse(self.booking.is_confirmed())


class ServiceSerializerTest(TestCase):
    """Test cases for ServiceSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )

    def test_service_serializer_fields(self):
        """Test service serializer fields."""
        serializer = ServiceSerializer(self.service)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('description', data)
        self.assertIn('category', data)
        self.assertIn('min_price', data)
        self.assertIn('max_price', data)

    def test_service_serializer_validation(self):
        """Test service serializer validation."""
        # Test valid data
        data = {
            'name': 'Test Service',
            'description': 'Test description',
            'category': 'Technology',
            'min_price': '100.00',
            'max_price': '500.00'
        }
        serializer = ServiceSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test invalid price range
        data = {
            'name': 'Test Service',
            'description': 'Test description',
            'category': 'Technology',
            'min_price': '500.00',
            'max_price': '100.00'
        }
        serializer = ServiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class SubServiceSerializerTest(TestCase):
    """Test cases for SubServiceSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )
        self.subservice = SubService.objects.create(
            service=self.service,
            name='Test Sub Service',
            description='Test sub service description',
            price=Decimal('150.00')
        )

    def test_subservice_serializer_fields(self):
        """Test subservice serializer fields."""
        serializer = SubServiceSerializer(self.subservice)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('description', data)
        self.assertIn('price', data)

    def test_subservice_serializer_validation(self):
        """Test subservice serializer validation."""
        # Test valid data
        data = {
            'name': 'Test Sub Service',
            'description': 'Test description',
            'price': '150.00'
        }
        serializer = SubServiceSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test invalid price
        data = {
            'name': 'Test Sub Service',
            'description': 'Test description',
            'price': '-150.00'
        }
        serializer = SubServiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ServiceRequestSerializerTest(TestCase):
    """Test cases for ServiceRequestSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.service_request = ServiceRequest.objects.create(
            user=self.user,
            title='Test Request',
            description='Test request description',
            category='Technology',
            price=Decimal('200.00')
        )

    def test_service_request_serializer_fields(self):
        """Test service request serializer fields."""
        serializer = ServiceRequestSerializer(self.service_request)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('category', data)
        self.assertIn('price', data)

    def test_service_request_serializer_validation(self):
        """Test service request serializer validation."""
        # Test valid data
        data = {
            'title': 'Test Request',
            'description': 'Test description',
            'category': 'Technology',
            'price': '200.00'
        }
        serializer = ServiceRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Test invalid price
        data = {
            'title': 'Test Request',
            'description': 'Test description',
            'category': 'Technology',
            'price': '-200.00'
        }
        serializer = ServiceRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ServiceAPITest(APITestCase):
    """Test cases for service API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )

    def test_get_all_services_details(self):
        """Test getting all services details."""
        url = reverse('get-all-services-details')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('provider_details', response.data)
        self.assertIn('services', response.data)

    def test_get_service_details(self):
        """Test getting service details."""
        url = reverse('get-service-details', args=[self.service.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('service_details', response.data)
        self.assertIn('sub_services', response.data)

    def test_add_service(self):
        """Test adding a new service."""
        url = reverse('add-service')
        data = {
            'name': 'New Service',
            'description': 'New service description',
            'category': 'Technology',
            'min_price': '100.00',
            'max_price': '500.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('service', response.data)

    def test_add_subservice(self):
        """Test adding a new subservice."""
        url = reverse('add-subservice', args=[self.service.id])
        data = {
            'name': 'New Sub Service',
            'description': 'New sub service description',
            'price': '150.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('subservice', response.data)


class ServiceViewSetTest(APITestCase):
    """Test cases for ServiceViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )

    def test_service_list(self):
        """Test service list endpoint."""
        url = reverse('service-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_service_detail(self):
        """Test service detail endpoint."""
        url = reverse('service-detail', args=[self.service.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.service.id)

    def test_service_update(self):
        """Test service update endpoint."""
        url = reverse('service-detail', args=[self.service.id])
        data = {
            'name': 'Updated Service',
            'description': 'Updated description',
            'category': 'Technology',
            'min_price': '150.00',
            'max_price': '600.00'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Service')


class SubServiceViewSetTest(APITestCase):
    """Test cases for SubServiceViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )
        self.subservice = SubService.objects.create(
            service=self.service,
            name='Test Sub Service',
            description='Test sub service description',
            price=Decimal('150.00')
        )

    def test_subservice_list(self):
        """Test subservice list endpoint."""
        url = reverse('subservice-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_subservice_detail(self):
        """Test subservice detail endpoint."""
        url = reverse('subservice-detail', args=[self.subservice.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.subservice.id)

    def test_subservice_update(self):
        """Test subservice update endpoint."""
        url = reverse('subservice-detail', args=[self.subservice.id])
        data = {
            'name': 'Updated Sub Service',
            'description': 'Updated description',
            'price': '200.00'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Sub Service')


class ServiceRequestViewSetTest(APITestCase):
    """Test cases for ServiceRequestViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.service_request = ServiceRequest.objects.create(
            user=self.user,
            title='Test Request',
            description='Test request description',
            category='Technology',
            price=Decimal('200.00')
        )

    def test_service_request_list(self):
        """Test service request list endpoint."""
        url = reverse('servicerequest-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_service_request_detail(self):
        """Test service request detail endpoint."""
        url = reverse('servicerequest-detail', args=[self.service_request.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.service_request.id)

    def test_service_request_create(self):
        """Test service request creation."""
        url = reverse('servicerequest-list')
        data = {
            'title': 'New Request',
            'description': 'New request description',
            'category': 'Technology',
            'price': '300.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)


class ServiceRequestBidViewSetTest(APITestCase):
    """Test cases for ServiceRequestBidViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service_request = ServiceRequest.objects.create(
            user=self.user,
            title='Test Request',
            description='Test request description',
            category='Technology',
            price=Decimal('200.00')
        )
        self.bid = ServiceRequestBid.objects.create(
            service_request=self.service_request,
            provider=self.provider,
            amount=Decimal('150.00'),
            proposal='Test proposal'
        )

    def test_bid_list(self):
        """Test bid list endpoint."""
        url = reverse('servicerequestbid-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_bid_detail(self):
        """Test bid detail endpoint."""
        url = reverse('servicerequestbid-detail', args=[self.bid.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.bid.id)

    def test_bid_create(self):
        """Test bid creation."""
        url = reverse('servicerequestbid-list')
        data = {
            'service_request': self.service_request.id,
            'amount': '180.00',
            'proposal': 'New proposal'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)


class BookingViewSetTest(APITestCase):
    """Test cases for BookingViewSet."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.provider = ServiceProvider.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='Test Address',
            business_category='Technology'
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name='Test Service',
            description='Test service description',
            category='Technology',
            min_price=Decimal('100.00'),
            max_price=Decimal('500.00')
        )
        self.booking = Booking.objects.create(
            user=self.user,
            service=self.service,
            booking_date='2024-01-15',
            status='confirmed'
        )

    def test_booking_list(self):
        """Test booking list endpoint."""
        url = reverse('booking-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_booking_detail(self):
        """Test booking detail endpoint."""
        url = reverse('booking-detail', args=[self.booking.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.booking.id)

    def test_booking_create(self):
        """Test booking creation."""
        url = reverse('booking-list')
        data = {
            'service': self.service.id,
            'booking_date': '2024-02-15',
            'notes': 'Test booking notes'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
