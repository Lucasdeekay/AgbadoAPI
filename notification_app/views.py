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


class GetUserNotificationsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_token(request)

        try:
            # Retrieve all notifications for the authenticated user, ordered by time
            notifications = Notification.objects.filter(user=user).order_by('-created_at')

            # Mark all notifications as read
            notifications.update(is_read=True)

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
                "message": 'A database error occurred while fetching notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateAllNotificationsReadStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
                "message": 'A database error occurred while updating notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteSingleNotificationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        user = get_user_from_token(request)

        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Get the notification, ensuring it belongs to the authenticated user
            notification = get_object_or_404(Notification, pk=pk, user=user)
            notification_id = notification.id # Store ID before deletion for response
            notification.delete()
            return Response({'message': f'Notification with ID {notification_id} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({"message": "Notification not found or does not belong to the user."}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({
                "message": 'A database error occurred while deleting the notification.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteMultipleNotificationsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request): # Using POST for batch deletion as DELETE with body can be tricky
        user = get_user_from_token(request)

        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        notification_ids = request.data.get('notification_ids', [])
        if not isinstance(notification_ids, list):
            return Response({"message": "Invalid data: 'notification_ids' must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        if not notification_ids:
            return Response({"message": "No notification IDs provided for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Delete notifications that belong to the user and are in the provided list of IDs
            deleted_count, _ = Notification.objects.filter(user=user, id__in=notification_ids).delete()

            if deleted_count == 0:
                return Response({"message": "No matching notifications found for deletion."}, status=status.HTTP_200_OK)

            return Response({
                'message': f'{deleted_count} notifications deleted successfully.'
            }, status=status.HTTP_200_OK)
        except DatabaseError:
            return Response({
                "message": 'A database error occurred while deleting multiple notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteAllNotificationsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = get_user_from_token(request)

        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Delete all notifications for the authenticated user
            deleted_count, _ = Notification.objects.filter(user=user).delete()
            return Response({
                'message': f'{deleted_count} notifications deleted successfully for user {user.email}.'
            }, status=status.HTTP_204_NO_CONTENT if deleted_count > 0 else status.HTTP_200_OK)
        except DatabaseError:
            return Response({
                "message": 'A database error occurred while deleting all notifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)