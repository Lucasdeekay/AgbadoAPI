from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from auth_app.views import get_user_from_token
from .models import Notification
from django.db import DatabaseError


class GetUserNotificationsView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_token(request)

        try:
            # Retrieve all notifications for the authenticated user, ordered by time
            notifications = Notification.objects.filter(user=user).order_by('-created_at')

            # Serialize the data to return the notifications
            notification_data = [
                {
                    'id': notification.id,
                    'message': notification.message,
                    'created_at': notification.created_at,
                    'is_read': notification.is_read
                }
                for notification in notifications
            ]

            return Response({
                'notifications': notification_data
            }, status=status.HTTP_200_OK)

        except DatabaseError:
            return Response({
                'error': 'A database error occurred while fetching notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateAllNotificationsReadStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = get_user_from_token(request)

        try:
            # Get all unread notifications for the user
            notifications = Notification.objects.filter(user=user, is_read=False)

            if not notifications.exists():
                return Response({
                    'message': 'No unread notifications found.'
                }, status=status.HTTP_200_OK)

            # Mark all notifications as read
            notifications.update(is_read=True)

            return Response({
                'message': 'All notifications have been marked as read.'
            }, status=status.HTTP_200_OK)

        except DatabaseError:
            return Response({
                'error': 'A database error occurred while updating notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
