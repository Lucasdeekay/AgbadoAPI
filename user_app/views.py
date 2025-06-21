from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from decouple import config

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication

from auth_app.models import KYC
from auth_app.serializers import KYCSerializer
from auth_app.utils import log_to_server, upload_to_cloudinary, write_to_file
from auth_app.views import get_user_from_token
from notification_app.models import Notification
from wallet_app.models import Wallet, Transaction
from wallet_app.serializers import TransactionSerializer

import logging


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')
class GetKYCDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch user details
        user = get_user_from_token(request)

        try:

            kyc_data = KYC.objects.get(user=user)
            if not kyc_data.exists():
                return Response({"message": "KYC details not found for this user."}, status=status.HTTP_404_NOT_FOUND)

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

@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

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

@method_decorator(csrf_exempt, name='dispatch')
class UpdateKYCView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_token(request)

        # Retrieve the user's KYC record
        try:
            kyc = KYC.objects.get_or_create(user=user)
        except ObjectDoesNotExist:
            return Response(
                {"message": "KYC record not found for this user."},
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
                {"message": "No data provided to update KYC."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update fields if they are provided
            if bvn:
                kyc.bvn = bvn
            if national_id:
                kyc.national_id = upload_to_cloudinary(national_id)
            if driver_license:
                kyc.driver_license = upload_to_cloudinary(driver_license)
            if proof_of_address:
                kyc.proof_of_address = upload_to_cloudinary(proof_of_address)


            kyc.status = 'Pending'  # Reset status to 'Pending' after update
            kyc.updated_at = timezone.now()

            kyc.save()

            Notification.objects.create(
                user=user,
                title="KYC Updated",
                message="Your KYC details have been updated and are pending review."
            )

            return Response(
                {"message": "KYC details updated successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
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
