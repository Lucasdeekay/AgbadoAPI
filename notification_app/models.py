"""
Notification app models for user notifications.

This module contains models for managing notifications sent to users.
"""

from datetime import datetime
from django.db import models
from auth_app.models import User


class Notification(models.Model):
    """
    Model representing a notification sent to a user.
    
    Manages user notifications including titles, messages, read status,
    and creation timestamps for tracking user engagement.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="notifications",
        help_text="User who receives the notification"
    )
    title = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Title of the notification"
    )
    message = models.TextField(
        help_text="Content/message of the notification"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the notification was created"
    )
    is_read = models.BooleanField(
        default=False, 
        help_text="Whether the notification has been read"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]

    def __str__(self) -> str:
        """String representation of the Notification."""
        title = self.title or "No Title"
        return f"Notification for {self.user.email} - {title}"

    def mark_as_read(self):
        """
        Mark the notification as read.
        
        Updates the is_read field to True.
        """
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        """
        Mark the notification as unread.
        
        Updates the is_read field to False.
        """
        self.is_read = False
        self.save(update_fields=['is_read'])

    @classmethod
    def get_unread_count(cls, user):
        """
        Get count of unread notifications for a user.
        
        Args:
            user: User instance
            
        Returns:
            int: Count of unread notifications
        """
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user):
        """
        Mark all notifications as read for a user.
        
        Args:
            user: User instance
            
        Returns:
            int: Number of notifications marked as read
        """
        return cls.objects.filter(user=user, is_read=False).update(is_read=True)
