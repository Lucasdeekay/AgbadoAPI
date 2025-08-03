"""
Notification app views for handling user notifications.

This module contains views for retrieving, updating, and deleting user notifications
with proper error handling and logging.
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from auth_app.views import get_user_from_token
from .models import Notification
from django.db import DatabaseError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class GetUserNotificationsView(APIView):
    """
    Get all notifications for the authenticated user.
    
    Retrieves all notifications for the user and marks them as read.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all notifications for the authenticated user.
        
        Returns all notifications ordered by creation date (newest first)
        and marks them as read.
        """
        try:
            user = get_user_from_token(request)

            # Retrieve all notifications for the authenticated user, ordered by time
            notifications = Notification.objects.filter(user=user).order_by('-created_at')

            # Mark all notifications as read
            notifications.update(is_read=True)

            # Serialize the data to return the notifications
            notification_data = [
                {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'created_at': notification.created_at,
                    'is_read': notification.is_read
                }
                for notification in notifications
            ]

            logger.info(f"Retrieved {len(notification_data)} notifications for user: {user.email}")
            return Response({
                'notifications': notification_data
            }, status=status.HTTP_200_OK)

        except DatabaseError:
            logger.error(f"Database error while fetching notifications for user: {user.email if 'user' in locals() else 'unknown'}")
            return Response({
                "message": 'A database error occurred while fetching notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Unexpected error fetching notifications: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UpdateAllNotificationsReadStatusView(APIView):
    """
    Mark all notifications as read for the authenticated user.
    
    Updates the read status of all unread notifications for the user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        """
        Mark all notifications as read for the authenticated user.
        """
        try:
            user = get_user_from_token(request)

            # Get all unread notifications for the user
            notifications = Notification.objects.filter(user=user, is_read=False)

            if not notifications.exists():
                return Response({
                    'message': 'No unread notifications found.'
                }, status=status.HTTP_200_OK)

            # Mark all notifications as read
            updated_count = notifications.update(is_read=True)

            logger.info(f"Marked {updated_count} notifications as read for user: {user.email}")
            return Response({
                'message': f'All {updated_count} notifications have been marked as read.'
            }, status=status.HTTP_200_OK)

        except DatabaseError:
            logger.error(f"Database error while updating notifications for user: {user.email if 'user' in locals() else 'unknown'}")
            return Response({
                "message": 'A database error occurred while updating notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Unexpected error updating notifications: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteSingleNotificationView(APIView):
    """
    Delete a single notification.
    
    Allows users to delete a specific notification by ID.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """
        Delete a single notification.
        
        URL parameter: pk (notification ID)
        """
        try:
            user = get_user_from_token(request)

            if not user:
                return Response(
                    {"message": "Authentication failed: User not found."}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get the notification, ensuring it belongs to the authenticated user
            notification = get_object_or_404(Notification, pk=pk, user=user)
            notification_id = notification.id
            notification.delete()
            
            logger.info(f"Notification {notification_id} deleted for user: {user.email}")
            return Response(
                {'message': f'Notification with ID {notification_id} deleted successfully.'}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Notification.DoesNotExist:
            return Response(
                {"message": "Notification not found or does not belong to the user."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError:
            logger.error(f"Database error while deleting notification {pk} for user: {user.email if 'user' in locals() else 'unknown'}")
            return Response({
                "message": 'A database error occurred while deleting the notification.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error deleting notification: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteMultipleNotificationsView(APIView):
    """
    Delete multiple notifications.
    
    Allows users to delete multiple notifications by providing a list of IDs.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Delete multiple notifications.
        
        Required fields: notification_ids (list of notification IDs)
        """
        try:
            user = get_user_from_token(request)

            if not user:
                return Response(
                    {"message": "Authentication failed: User not found."}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            notification_ids = request.data.get('notification_ids', [])
            if not isinstance(notification_ids, list):
                return Response(
                    {"message": "Invalid data: 'notification_ids' must be a list."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not notification_ids:
                return Response(
                    {"message": "No notification IDs provided for deletion."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete notifications that belong to the user and are in the provided list of IDs
            deleted_count, _ = Notification.objects.filter(user=user, id__in=notification_ids).delete()

            if deleted_count == 0:
                return Response(
                    {"message": "No matching notifications found for deletion."}, 
                    status=status.HTTP_200_OK
                )

            logger.info(f"Deleted {deleted_count} notifications for user: {user.email}")
            return Response({
                'message': f'{deleted_count} notifications deleted successfully.'
            }, status=status.HTTP_200_OK)
            
        except DatabaseError:
            logger.error(f"Database error while deleting multiple notifications for user: {user.email if 'user' in locals() else 'unknown'}")
            return Response({
                "message": 'A database error occurred while deleting multiple notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error deleting multiple notifications: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteAllNotificationsView(APIView):
    """
    Delete all notifications for the authenticated user.
    
    Removes all notifications belonging to the user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """
        Delete all notifications for the authenticated user.
        """
        try:
            user = get_user_from_token(request)

            if not user:
                return Response(
                    {"message": "Authentication failed: User not found."}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Delete all notifications for the authenticated user
            deleted_count, _ = Notification.objects.filter(user=user).delete()
            
            logger.info(f"Deleted {deleted_count} notifications for user: {user.email}")
            return Response({
                'message': f'{deleted_count} notifications deleted successfully for user {user.email}.'
            }, status=status.HTTP_204_NO_CONTENT if deleted_count > 0 else status.HTTP_200_OK)
            
        except DatabaseError:
            logger.error(f"Database error while deleting all notifications for user: {user.email if 'user' in locals() else 'unknown'}")
            return Response({
                "message": 'A database error occurred while deleting all notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error deleting all notifications: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)