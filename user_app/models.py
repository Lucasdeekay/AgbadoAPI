from django.db import models
from django.utils import timezone
from auth_app.models import User

class DailyTask(models.Model):
    TASK_TYPES = [
        ('WatchVideo', 'Watch Video'),
        ('FollowSocialMedia', 'Follow Social Media'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    youtube_link = models.URLField(null=True, blank=True)  # For video tasks
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class TaskCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="completed_tasks")
    task = models.ForeignKey(DailyTask, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)
    otp_verified = models.BooleanField(default=False)  # Verification after watching video

    def __str__(self):
        return f"{self.user.email} completed {self.task.title}"

class UserReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rewards")
    points = models.PositiveIntegerField(default=0)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - Points: {self.points}"

class LeisureAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leisure_access")
    instagram_handle = models.CharField(max_length=100)
    youtube_channel = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Leisure Access - {self.user.email} Verified: {self.is_verified}"

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('FollowInstagram', 'Follow Instagram'),
        ('FollowYouTube', 'Follow YouTube'),
        ('ServiceRequest', 'Service Request'),
        ('TaskCompletion', 'Task Completion'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Activity: {self.activity_type}"
