from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from auth_app.views import get_user_from_token
from notification_app.models import Notification
from wallet_app.models import Wallet, Transaction
from wallet_app.serializers import TransactionSerializer


class DashboardView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

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
                "is_verified": user.is_verified,
                "profile_picture": (
                    request.build_absolute_uri(user.profile_picture.url)
                    if user.profile_picture and user.profile_picture.url
                    else None
                ),
            }
        except Exception as e:
            return Response({"error": f"Error fetching user details: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Fetch wallet details
            wallet = Wallet.objects.get(user=user)
            wallet_data = {
                "balance": wallet.balance,
                "last_updated": wallet.updated_at,
            }
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error fetching wallet details: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Fetch last 5 transactions
            transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:5]
            transactions_data = TransactionSerializer(transactions, many=True).data
        except Exception as e:
            return Response({"error": f"Error fetching transactions: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Check if the user has any unread notifications
            has_unread_notifications = Notification.objects.filter(user=user, is_read=False).exists()
        except DatabaseError:
            return Response({"error": "Error checking notifications."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Error fetching notification status: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Combine data into response
        response_data = {
            "user_details": user_data,
            "wallet_details": wallet_data,
            "recent_transactions": transactions_data,
            "has_unread_notifications": has_unread_notifications,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class UpdateUserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def put(self, request):
        user = get_user_from_token(request)

        # Extract data from the request
        phone_number = request.data.get('phone_number')
        state = request.data.get('state')
        profile_picture = request.FILES.get('profile_picture')

        # Handle empty requests gracefully
        if not phone_number and not state and not profile_picture:
            return Response(
                {"error": "No data provided to update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update fields if they are provided
            if phone_number:
                user.phone_number = phone_number
            if state:
                user.state = state
            if profile_picture:
                user.profile_picture = profile_picture

            user.save()

            return Response(
                {"message": "User profile updated successfully."},
                status=status.HTTP_200_OK
            )

        except IntegrityError:
            return Response(
                {"error": "Phone number must be unique."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateKYCView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def put(self, request):
        user = get_user_from_token(request)

        # Retrieve the user's KYC record
        try:
            kyc = user.kyc
        except ObjectDoesNotExist:
            return Response(
                {"error": "KYC record not found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Extract data from the request
        national_id = request.FILES.get('national_id')
        bvn = request.data.get('bvn')
        driver_license = request.FILES.get('driver_license')
        proof_of_address = request.FILES.get('proof_of_address')

        # Handle empty requests gracefully
        if not any([national_id, bvn, driver_license, proof_of_address]):
            return Response(
                {"error": "No data provided to update KYC."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update fields if they are provided
            if national_id:
                kyc.national_id = national_id
            if bvn:
                kyc.bvn = bvn
            if driver_license:
                kyc.driver_license = driver_license
            if proof_of_address:
                kyc.proof_of_address = proof_of_address

            kyc.status = 'Pending'  # Reset status to 'Pending' after update
            kyc.updated_at = timezone.now()

            kyc.save()

            return Response(
                {"message": "KYC details updated successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Change the user's password after validating the current password.
        User provides current_password and new_password.
        """
        user = get_user_from_token(request)

        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({"error": "Both current_password and new_password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate the current password
        if not user.check_password(current_password):
            return Response({"error": "The current password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password has been successfully changed."}, status=status.HTTP_200_OK)
