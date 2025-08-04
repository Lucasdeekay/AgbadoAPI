"""
User app models for task management, rewards, and user activities.

This module contains models for managing daily tasks, user rewards,
activities, leisure access, and gift systems.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from auth_app.models import User

class DailyTask(models.Model):
    """
    Model for daily tasks that users can complete to earn points.
    
    Tasks can be video watching or social media following activities.
    """
    TASK_TYPES = [
        ('WatchVideo', 'Watch Video'),
        ('FollowSocialMedia', 'Follow Social Media'),
    ]
    
    title = models.CharField(max_length=255, help_text="Task title")
    description = models.TextField(help_text="Detailed task description")
    task_type = models.CharField(
        max_length=20, 
        choices=TASK_TYPES,
        help_text="Type of task"
    )
    youtube_link = models.URLField(
        null=True, 
        blank=True,
        help_text="YouTube video link for video tasks"
    )
    points = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Points awarded for completing this task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether this task is currently available")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Daily Task"
        verbose_name_plural = "Daily Tasks"

    def __str__(self):
        return self.title

class TaskCompletion(models.Model):
    """
    Model for tracking task completions by users.
    
    Records when a user completes a task and whether OTP verification was done.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="completed_tasks",
        help_text="User who completed the task"
    )
    task = models.ForeignKey(
        DailyTask, 
        on_delete=models.CASCADE, 
        related_name="completions",
        help_text="Task that was completed"
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    otp_verified = models.BooleanField(
        default=False,
        help_text="Whether OTP verification was completed"
    )

    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Task Completion"
        verbose_name_plural = "Task Completions"
        unique_together = ['user', 'task']  # Prevent duplicate completions

    def __str__(self):
        return f"{self.user.email} completed {self.task.title}"

class UserReward(models.Model):
    """
    Model for tracking user reward points and redemption status.
    
    Manages the points system for users and tracks when rewards are redeemed.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="reward_account",
        help_text="User associated with this reward account"
    )
    points = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current points balance"
    )
    redeemed = models.BooleanField(default=False, help_text="Whether points have been redeemed")
    redeemed_at = models.DateTimeField(null=True, blank=True, help_text="When points were redeemed")

    class Meta:
        verbose_name = "User Reward"
        verbose_name_plural = "User Rewards"

    def __str__(self):
        return f"{self.user.email} - Points: {self.points}"

class LeisureAccess(models.Model):
    """
    Model for managing user access to leisure/social media features.
    
    Tracks social media handles and verification status for leisure activities.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="leisure_access",
        help_text="User associated with this leisure access"
    )
    instagram_handle = models.CharField(
        max_length=100,
        help_text="User's Instagram handle"
    )
    youtube_channel = models.CharField(
        max_length=100,
        help_text="User's YouTube channel name"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether social media accounts are verified"
    )
    verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When verification was completed"
    )

    class Meta:
        verbose_name = "Leisure Access"
        verbose_name_plural = "Leisure Access"

    def __str__(self):
        return f"Leisure Access - {self.user.email} Verified: {self.is_verified}"

class UserActivity(models.Model):
    """
    Model for tracking user activities and actions.
    
    Logs various user activities for analytics and tracking purposes.
    """
    ACTIVITY_TYPES = [
        ('FollowInstagram', 'Follow Instagram'),
        ('FollowYouTube', 'Follow YouTube'),
        ('ServiceRequest', 'Service Request'),
        ('TaskCompletion', 'Task Completion'),
        ('ProfileUpdate', 'Profile Update'),
        ('KYCUpdate', 'KYC Update'),
        ('GiftClaimed', 'Gift Claimed'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="activities",
        help_text="User who performed the activity"
    )
    activity_type = models.CharField(
        max_length=20, 
        choices=ACTIVITY_TYPES,
        help_text="Type of activity performed"
    )
    description = models.TextField(
        null=True, 
        blank=True,
        help_text="Additional details about the activity"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"{self.user.email} - Activity: {self.activity_type}"

class Gift(models.Model):
    """
    Model for gifts that users can claim with their reward points.
    
    Manages gift information including images and point requirements.
    """
    name = models.CharField(
        max_length=255,
        help_text="Name of the gift"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed description of the gift"
    )
    image = models.ImageField(
        upload_to='gifts/',
        help_text="Gift image"
    )
    coin_amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Points required to claim this gift"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this gift is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['coin_amount']
        verbose_name = "Gift"
        verbose_name_plural = "Gifts"

    def __str__(self):
        return self.name

class UserGift(models.Model):
    """
    Model for tracking gifts claimed by users.
    
    Manages the relationship between users and gifts they've claimed,
    including delivery status and tracking.
    """
    DELIVERY_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="won_gifts",
        help_text="User who claimed the gift"
    )
    gift = models.ForeignKey(
        Gift, 
        on_delete=models.CASCADE, 
        related_name="winners",
        help_text="Gift that was claimed"
    )
    date_won = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(
        max_length=20, 
        choices=DELIVERY_STATUS_CHOICES, 
        default='Pending',
        help_text="Current delivery status"
    )
    delivery_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the gift was delivered"
    )

    class Meta:
        ordering = ['-date_won']
        verbose_name = "User Gift"
        verbose_name_plural = "User Gifts"

    def __str__(self):
        return f"{self.user.email} won {self.gift.name}"
    