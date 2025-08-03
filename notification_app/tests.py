"""
Tests for notification_app models, serializers, and views.

This module contains comprehensive tests for notification-related functionality
including notification creation, management, and user interactions.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone

from .models import Notification
from .serializers import (
    NotificationSerializer, NotificationListSerializer, NotificationDetailSerializer
)

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message."
        )

    def test_notification_creation(self):
        """Test that a notification can be created."""
        self.assertEqual(self.notification.user, self.user)
        self.assertEqual(self.notification.title, "Test Notification")
        self.assertEqual(self.notification.message, "This is a test notification message.")
        self.assertFalse(self.notification.is_read)

    def test_notification_string_representation(self):
        """Test the string representation of a notification."""
        expected = f"Notification for {self.user.email} - Test Notification"
        self.assertEqual(str(self.notification), expected)

    def test_notification_without_title(self):
        """Test notification without title."""
        notification = Notification.objects.create(
            user=self.user,
            message="Notification without title"
        )
        expected = f"Notification for {self.user.email} - No Title"
        self.assertEqual(str(notification), expected)

    def test_mark_as_read(self):
        """Test marking notification as read."""
        self.assertFalse(self.notification.is_read)
        self.notification.mark_as_read()
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_as_unread(self):
        """Test marking notification as unread."""
        self.notification.mark_as_read()
        self.notification.mark_as_unread()
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_get_unread_count(self):
        """Test getting unread notification count."""
        # Create another unread notification
        Notification.objects.create(
            user=self.user,
            title="Another Notification",
            message="Another test message."
        )
        
        unread_count = Notification.get_unread_count(self.user)
        self.assertEqual(unread_count, 2)

    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        # Create another notification
        Notification.objects.create(
            user=self.user,
            title="Another Notification",
            message="Another test message."
        )
        
        updated_count = Notification.mark_all_as_read(self.user)
        self.assertEqual(updated_count, 2)
        
        # Verify all are now read
        unread_count = Notification.get_unread_count(self.user)
        self.assertEqual(unread_count, 0)

    def test_notification_ordering(self):
        """Test that notifications are ordered by creation date."""
        notification2 = Notification.objects.create(
            user=self.user,
            title="Second Notification",
            message="Second test message."
        )
        
        notifications = Notification.objects.all()
        self.assertEqual(notifications[0], notification2)  # Newer first


class NotificationSerializerTest(TestCase):
    """Test cases for NotificationSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message."
        )
        self.serializer = NotificationSerializer(instance=self.notification)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'title', 'message', 'created_at', 'is_read'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_title_field_content(self):
        """Test the title field content."""
        data = self.serializer.data
        self.assertEqual(data['title'], self.notification.title)

    def test_message_field_content(self):
        """Test the message field content."""
        data = self.serializer.data
        self.assertEqual(data['message'], self.notification.message)

    def test_validate_message_empty(self):
        """Test message validation with empty message."""
        serializer = NotificationSerializer()
        with self.assertRaises(Exception):
            serializer.validate_message("")

    def test_validate_message_too_long(self):
        """Test message validation with too long message."""
        serializer = NotificationSerializer()
        long_message = "x" * 1001
        with self.assertRaises(Exception):
            serializer.validate_message(long_message)

    def test_validate_title_too_long(self):
        """Test title validation with too long title."""
        serializer = NotificationSerializer()
        long_title = "x" * 201
        with self.assertRaises(Exception):
            serializer.validate_title(long_title)


class NotificationListSerializerTest(TestCase):
    """Test cases for NotificationListSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message."
        )
        self.serializer = NotificationListSerializer(instance=self.notification)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'title', 'message', 'created_at', 'is_read'
        }
        self.assertCountEqual(data.keys(), expected_fields)

    def test_excludes_user_field(self):
        """Test that user field is excluded from list view."""
        data = self.serializer.data
        self.assertNotIn('user', data)


class NotificationDetailSerializerTest(TestCase):
    """Test cases for NotificationDetailSerializer."""

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
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message."
        )
        self.serializer = NotificationDetailSerializer(instance=self.notification)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        expected_fields = {
            'id', 'user', 'user_email', 'user_name', 'title', 'message', 
            'created_at', 'is_read'
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


class NotificationAppViewsTest(APITestCase):
    """Test cases for notification app views."""

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
        
        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            title="Test Notification 1",
            message="First test message."
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            title="Test Notification 2",
            message="Second test message.",
            is_read=True
        )

    def test_get_user_notifications(self):
        """Test getting user notifications."""
        url = reverse('get_user_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('notifications', response.data)
        self.assertEqual(len(response.data['notifications']), 2)

    def test_update_all_notifications_read_status(self):
        """Test updating all notifications read status."""
        url = reverse('update_all_notifications_read_status')
        data = {'is_read': True}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_delete_single_notification(self):
        """Test deleting a single notification."""
        url = reverse('delete_single_notification', args=[self.notification1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_delete_multiple_notifications(self):
        """Test deleting multiple notifications."""
        url = reverse('delete_multiple_notifications')
        data = {'notification_ids': [self.notification1.id, self.notification2.id]}
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_delete_all_notifications(self):
        """Test deleting all notifications."""
        url = reverse('delete_all_notifications')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_get_user_notifications_unauthenticated(self):
        """Test getting notifications without authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('get_user_notifications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationAppViewSetsTest(APITestCase):
    """Test cases for notification app ViewSets."""

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
        
        # Create test notification
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message."
        )

    def test_notification_list(self):
        """Test listing notifications."""
        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_notification_detail(self):
        """Test getting notification details."""
        url = reverse('notification-detail', args=[self.notification.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.notification.title)

    def test_notification_create(self):
        """Test creating a notification."""
        url = reverse('notification-list')
        data = {
            'user': self.user.id,
            'title': 'New Notification',
            'message': 'New notification message.'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Notification')

    def test_notification_update(self):
        """Test updating a notification."""
        url = reverse('notification-detail', args=[self.notification.id])
        data = {'is_read': True}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])

    def test_notification_delete(self):
        """Test deleting a notification."""
        url = reverse('notification-detail', args=[self.notification.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_notification_filter_by_read_status(self):
        """Test filtering notifications by read status."""
        url = reverse('notification-list')
        response = self.client.get(url, {'is_read': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_notification_search(self):
        """Test searching notifications."""
        url = reverse('notification-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_notification_ordering(self):
        """Test ordering notifications."""
        # Create another notification
        Notification.objects.create(
            user=self.user,
            title="Another Notification",
            message="Another message."
        )
        
        url = reverse('notification-list')
        response = self.client.get(url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
