"""
User app views for handling user-related operations.

This module contains views for user dashboard, profile management, KYC operations,
and other user-specific functionality.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from auth_app.models import KYC
from auth_app.serializers import KYCSerializer
from decouple import config
from auth_app.utils import upload_to_cloudinary
from auth_app.views import get_user_from_token
from notification_app.models import Notification
from wallet_app.models import Wallet, Transaction
from wallet_app.serializers import TransactionSerializer

import logging

logger = logging.getLogger(__name__)



class DashboardView(APIView):
    """
    Dashboard view for authenticated users.
    
    Returns user details, wallet information, recent transactions,
    and notification status.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Fetch user details
            user = get_user_from_token(request)
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "state": user.state,
                "is_verified": user.is_verified,
                "paystack_key": config('PAYSTACK_SECRET_KEY'),
                "profile_picture": user.profile_picture,
            }
        except Exception as e:
            return Response({"message": f"Error fetching user details: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Fetch wallet details
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet_data = {
                "balance": wallet.balance,
                "last_updated": wallet.updated_at,
            }
        except Wallet.DoesNotExist:
            return Response({"message": "Wallet not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": f"Error fetching wallet details: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Fetch last 5 transactions
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
            transactions_data = TransactionSerializer(transactions, many=True).data
        except Exception as e:
            transactions_data = []

        try:
            # Check if the user has any unread notifications
            has_unread_notifications = Notification.objects.filter(user=user, is_read=False).exists()
        except Exception as e:
            has_unread_notifications = False

            # Combine data into response
        response_data = {
            "user_details": user_data,
            "wallet_details": wallet_data,
            "recent_transactions": transactions_data,
            "has_unread_notifications": has_unread_notifications,
        }

        return Response(response_data, status=status.HTTP_200_OK)



class GetKYCDetailsView(APIView):
    """
    Retrieve KYC details for the authenticated user.
    
    Returns the user's KYC information including verification status
    and document details.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch user details
        user = get_user_from_token(request)

        try:

            kyc_data = KYC.objects.get(user=user)
            
            kyc_data = {
                "national_id": kyc_data.national_id,
                "bvn": kyc_data.bvn,
                "driver_license": kyc_data.driver_license,
                "proof_of_address": kyc_data.proof_of_address,
                "status": kyc_data.status,
                "updated_at": kyc_data.updated_at,
                "verified_at": kyc_data.verified_at,
            }
            return Response({
                'kyc_data': kyc_data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"message": f"Error fetching kyc details: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateUserProfileView(APIView):
    """
    Update user profile information.
    
    Allows users to update their phone number, state, and profile picture.
    Creates a notification when profile is successfully updated.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_token(request)

        # Extract data from the request
        phone_number = request.data.get('phone_number')
        state = request.data.get('state')
        profile_picture = request.FILES.get('profile_picture')

        # Handle empty requests gracefully
        if not phone_number and not state and not profile_picture:
            return Response(
                {"message": "No data provided to update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update fields if they are provided
            if phone_number:
                user.phone_number = phone_number
            if state:
                user.state = state
            if profile_picture:
                cloud_url = upload_to_cloudinary(profile_picture)
                print(f"Uploaded image URL: {cloud_url}")

                user.profile_picture = cloud_url

            user.save()

            Notification.objects.create(
                user=user,
                title="Profile Updated",
                message="Your profile has been updated successfully."
            )

            return Response(
                {"message": "User profile updated successfully."},
                status=status.HTTP_200_OK
            )

        except IntegrityError:
            return Response(
                {"message": "Phone number is already in use by another user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateKYCView(APIView):
    """
    Update KYC information for the authenticated user.
    
    Handles KYC document uploads and updates verification status.
    Supports partial updates of KYC information.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Uncomment and set this up as needed

    def post(self, request):
        user = get_user_from_token(request)

        # 1. Get or create the KYC instance correctly.
        # get_or_create returns a tuple: (object, created_boolean).
        # We need to unpack it to get the actual KYC model object.
        kyc_instance, created = KYC.objects.get_or_create(user=user)

        # 2. Instantiate the serializer with the KYC instance and request data.
        # Pass `partial=True` to allow updating only some fields.
        # Crucially, pass `context={'request': request}` so the serializer can access request.FILES.
        serializer = KYCSerializer(
            kyc_instance,  # The existing KYC instance to update
            data=request.data,
            partial=True,  # Allow partial updates
            context={'request': request} # Essential for file uploads within the serializer
        )

        # 3. Validate the incoming data using the serializer.
        if serializer.is_valid():
            try:
                # 4. Save the serializer. This will automatically call the serializer's
                # .update() method (since an instance was passed to the constructor).
                # Your serializer's update method now handles the file uploads and field updates.
                serializer.save()

                # 5. Optionally, update KYC status and timestamp *after* serializer save.
                # If 'status' and 'updated_at' are consistently set to 'Pending' after any update,
                # you can keep this logic here. Alternatively, consider moving this into the
                # serializer's `update` method if it's tightly coupled to the data update.
                if kyc_instance.status != 'Pending': # Only update if status needs changing
                     kyc_instance.status = 'Pending'
                     kyc_instance.updated_at = timezone.now()
                     kyc_instance.save(update_fields=['status', 'updated_at']) # Save specific fields for efficiency

                # 6. Create notification (this can remain in the view as a side effect).
                Notification.objects.create(
                    user=user,
                    title="KYC Updated",
                    message="Your KYC details have been updated and are pending review."
                )

                # 7. Return a success response with the serialized data.
                return Response(
                    {"message": "KYC details updated successfully.", "kyc_data": serializer.data},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                # Catch any unexpected errors that might occur during serializer.save()
                # or subsequent operations.
                return Response(
                    {"message": f"An internal server error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # 8. If validation fails, return the errors from the serializer.
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ChangePasswordView(APIView):
    """
    Change user password.
    
    Allows authenticated users to change their password.
    Validates old password before allowing the change.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Change the user's password after validating the current password.
        User provides current_password and new_password.
        """
        user = get_user_from_token(request)

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({"message": "Both current_password and new_password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate the current password
        if not user.check_password(current_password):
            return Response({"message": "The current password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        Notification.objects.create(
            user=user,
            title="Password Changed",
            message="Your password has been successfully changed."
        )

        return Response({"message": "Password has been successfully changed."}, status=status.HTTP_200_OK)


class GetReferralCode(APIView):
    """
    Get user's referral code.
    
    Returns the unique referral code for the authenticated user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_token(request)
        referral_code = user.referral_code
        return Response({"referral_code": referral_code}, status=status.HTTP_200_OK)
