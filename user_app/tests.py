"""
Tests for user_app models, views, and serializers.

This module contains comprehensive tests for user-related functionality
including tasks, rewards, activities, and gifts.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import (
    DailyTask, TaskCompletion, UserReward, UserActivity, 
    LeisureAccess, Gift, UserGift
)
from .serializers import (
    DailyTaskSerializer, TaskCompletionSerializer, UserRewardSerializer,
    UserActivitySerializer, LeisureAccessSerializer, GiftSerializer, UserGiftSerializer
)

User = get_user_model()


class DailyTaskModelTest(TestCase):
    """Test cases for DailyTask model."""

    def setUp(self):
        """Set up test data."""
        self.task = DailyTask.objects.create(
            title="Test Task",
            description="A test task for testing",
            task_type="WatchVideo",
            points=50,
            youtube_link="https://youtube.com/watch?v=test"
        )

    def test_task_creation(self):
        """Test that a task can be created."""
        self.assertEqual(self.task.title, "Test Task")
        self.assertEqual(self.task.points, 50)
        self.assertTrue(self.task.is_active)

    def test_task_string_representation(self):
        """Test the string representation of a task."""
        self.assertEqual(str(self.task), "Test Task")

    def test_task_ordering(self):
        """Test that tasks are ordered by creation date."""
        task2 = DailyTask.objects.create(
            title="Second Task",
            description="Another test task",
            task_type="FollowSocialMedia",
            points=25
        )
        tasks = DailyTask.objects.all()
        self.assertEqual(tasks[0], task2)  # Newer task first due to ordering


class TaskCompletionModelTest(TestCase):
    """Test cases for TaskCompletion model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.task = DailyTask.objects.create(
            title="Test Task",
            description="A test task",
            task_type="WatchVideo",
            points=50
        )
        self.completion = TaskCompletion.objects.create(
            user=self.user,
            task=self.task,
            otp_verified=True
        )

    def test_completion_creation(self):
        """Test that a task completion can be created."""
        self.assertEqual(self.completion.user, self.user)
        self.assertEqual(self.completion.task, self.task)
        self.assertTrue(self.completion.otp_verified)

    def test_completion_string_representation(self):
        """Test the string representation of a completion."""
        expected = f"{self.user.email} completed {self.task.title}"
        self.assertEqual(str(self.completion), expected)

    def test_unique_user_task_constraint(self):
        """Test that a user cannot complete the same task twice."""
        with self.assertRaises(Exception):
            TaskCompletion.objects.create(
                user=self.user,
                task=self.task,
                otp_verified=False
            )


class UserRewardModelTest(TestCase):
    """Test cases for UserReward model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.reward = UserReward.objects.create(
            user=self.user,
            points=100
        )

    def test_reward_creation(self):
        """Test that a user reward can be created."""
        self.assertEqual(self.reward.user, self.user)
        self.assertEqual(self.reward.points, 100)
        self.assertFalse(self.reward.redeemed)

    def test_reward_string_representation(self):
        """Test the string representation of a reward."""
        expected = f"{self.user.email} - Points: 100"
        self.assertEqual(str(self.reward), expected)

    def test_one_to_one_relationship(self):
        """Test that a user can only have one reward account."""
        with self.assertRaises(Exception):
            UserReward.objects.create(
                user=self.user,
                points=50
            )


class GiftModelTest(TestCase):
    """Test cases for Gift model."""

    def setUp(self):
        """Set up test data."""
        self.gift = Gift.objects.create(
            name="Test Gift",
            coin_amount=200
        )

    def test_gift_creation(self):
        """Test that a gift can be created."""
        self.assertEqual(self.gift.name, "Test Gift")
        self.assertEqual(self.gift.coin_amount, 200)

    def test_gift_string_representation(self):
        """Test the string representation of a gift."""
        self.assertEqual(str(self.gift), "Test Gift")

    def test_gift_ordering(self):
        """Test that gifts are ordered by coin amount."""
        gift2 = Gift.objects.create(
            name="Cheaper Gift",
            coin_amount=100
        )
        gifts = Gift.objects.all()
        self.assertEqual(gifts[0], gift2)  # Cheaper gift first


class DailyTaskSerializerTest(TestCase):
    """Test cases for DailyTaskSerializer."""

    def setUp(self):
        """Set up test data."""
        self.task = DailyTask.objects.create(
            title="Test Task",
            description="A test task",
            task_type="WatchVideo",
            points=50
        )
        self.serializer = DailyTaskSerializer(instance=self.task)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'title', 'description', 'task_type', 'youtube_link', 
             'points', 'created_at', 'is_active']
        )

    def test_title_field_content(self):
        """Test the title field content."""
        data = self.serializer.data
        self.assertEqual(data['title'], self.task.title)

    def test_points_field_content(self):
        """Test the points field content."""
        data = self.serializer.data
        self.assertEqual(data['points'], self.task.points)


class TaskCompletionSerializerTest(TestCase):
    """Test cases for TaskCompletionSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )
        self.task = DailyTask.objects.create(
            title="Test Task",
            description="A test task",
            task_type="WatchVideo",
            points=50
        )
        self.completion = TaskCompletion.objects.create(
            user=self.user,
            task=self.task,
            otp_verified=True
        )
        self.serializer = TaskCompletionSerializer(instance=self.completion)

    def test_contains_expected_fields(self):
        """Test that the serializer contains expected fields."""
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(),
            ['id', 'user', 'task', 'completed_at', 'otp_verified']
        )

    def test_nested_task_data(self):
        """Test that task data is properly nested."""
        data = self.serializer.data
        self.assertIn('task', data)
        self.assertEqual(data['task']['title'], self.task.title)


class UserAppViewsTest(APITestCase):
    """Test cases for user app views."""

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

    def test_dashboard_view_authenticated(self):
        """Test dashboard view with authenticated user."""
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_details', response.data)
        self.assertIn('wallet_details', response.data)

    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view without authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_referral_code_authenticated(self):
        """Test getting referral code with authenticated user."""
        url = reverse('get_referral_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('referral_code', response.data)

    def test_get_referral_code_unauthenticated(self):
        """Test getting referral code without authentication."""
        self.client.credentials()  # Remove authentication
        url = reverse('get_referral_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAppViewSetsTest(APITestCase):
    """Test cases for user app ViewSets."""

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
        
        # Create test data
        self.task = DailyTask.objects.create(
            title="Test Task",
            description="A test task",
            task_type="WatchVideo",
            points=50
        )
        self.gift = Gift.objects.create(
            name="Test Gift",
            coin_amount=100
        )
        self.user_reward = UserReward.objects.create(
            user=self.user,
            points=200
        )

    def test_daily_task_list(self):
        """Test listing daily tasks."""
        url = reverse('dailytask-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_daily_task_filter_by_type(self):
        """Test filtering daily tasks by type."""
        url = reverse('dailytask-list')
        response = self.client.get(url, {'task_type': 'WatchVideo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_gift_list(self):
        """Test listing gifts."""
        url = reverse('gift-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_gift_creation_with_sufficient_points(self):
        """Test creating a user gift with sufficient points."""
        url = reverse('usergift-list')
        data = {'gift': self.gift.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that points were deducted
        self.user_reward.refresh_from_db()
        self.assertEqual(self.user_reward.points, 100)  # 200 - 100

    def test_user_gift_creation_insufficient_points(self):
        """Test creating a user gift with insufficient points."""
        # Reduce user points
        self.user_reward.points = 50
        self.user_reward.save()
        
        url = reverse('usergift-list')
        data = {'gift': self.gift.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Not enough points', response.data['detail'])


class UserActivityTest(TestCase):
    """Test cases for user activity tracking."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )

    def test_activity_creation(self):
        """Test creating user activities."""
        activity = UserActivity.objects.create(
            user=self.user,
            activity_type="ProfileUpdate",
            description="User updated their profile"
        )
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.activity_type, "ProfileUpdate")

    def test_activity_ordering(self):
        """Test that activities are ordered by creation date."""
        activity1 = UserActivity.objects.create(
            user=self.user,
            activity_type="ProfileUpdate"
        )
        activity2 = UserActivity.objects.create(
            user=self.user,
            activity_type="KYCUpdate"
        )
        activities = UserActivity.objects.all()
        self.assertEqual(activities[0], activity2)  # Newer activity first


class LeisureAccessTest(TestCase):
    """Test cases for leisure access functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            phone_number="1234567890",
            state="Test State"
        )

    def test_leisure_access_creation(self):
        """Test creating leisure access."""
        leisure = LeisureAccess.objects.create(
            user=self.user,
            instagram_handle="@testuser",
            youtube_channel="Test Channel"
        )
        self.assertEqual(leisure.user, self.user)
        self.assertEqual(leisure.instagram_handle, "@testuser")
        self.assertFalse(leisure.is_verified)

    def test_leisure_access_verification(self):
        """Test verifying leisure access."""
        leisure = LeisureAccess.objects.create(
            user=self.user,
            instagram_handle="@testuser",
            youtube_channel="Test Channel"
        )
        leisure.is_verified = True
        leisure.save()
        self.assertTrue(leisure.is_verified)
