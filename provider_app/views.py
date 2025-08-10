"""
Provider app views for handling service provider operations.

This module contains views for creating, updating, and retrieving service provider profiles
with proper error handling and logging.
"""

from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from auth_app.utils import upload_to_cloudinary
from auth_app.views import get_user_from_token
from notification_app.models import Notification
from provider_app.models import ServiceProvider

import logging

logger = logging.getLogger(__name__)



class CreateServiceProviderView(APIView):
    """
    Create a new service provider profile.
    
    Allows users to create their service provider profile with company details.
    """
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new service provider profile.
        
        Required fields: company_name, company_address, business_category
        Optional fields: company_description, company_phone_no, company_email, 
                        company_logo, opening_hour, closing_hour
        """
        try:
            user = get_user_from_token(request)

            if hasattr(user, "provider_profile"):
                return Response(
                    {"message": "User already has a provider profile."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            company_name = request.data.get("company_name")
            company_address = request.data.get("company_address")
            company_description = request.data.get("company_description")
            company_phone_no = request.data.get("company_phone_no")
            company_email = request.data.get("company_email")
            business_category = request.data.get("business_category")
            company_logo = request.FILES.get("company_logo")
            opening_hour = request.data.get("opening_hour")
            closing_hour = request.data.get("closing_hour")

            if not company_name or not company_address or not business_category:
                return Response(
                    {"message": "All required fields must be provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                logo_url = None
                if company_logo:
                    logo_url = upload_to_cloudinary(company_logo)

                service_provider = ServiceProvider.objects.create(
                    user=user,
                    company_name=company_name,
                    company_address=company_address,
                    company_description=company_description,
                    company_phone_no=company_phone_no,
                    company_email=company_email,
                    business_category=business_category,
                    company_logo=logo_url,
                    opening_hour=opening_hour,
                    closing_hour=closing_hour,
                )

                Notification.objects.create(
                    user=user,
                    title="Service Provider Profile Created",
                    message="Your service provider profile has been created successfully.",
                )

                logger.info(f"Service provider profile created for user: {user.email}")
                return Response(
                    {"message": "Service provider profile created successfully."},
                    status=status.HTTP_201_CREATED,
                )

            except IntegrityError:
                return Response(
                    {"message": "A service provider with this contact information already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Error creating service provider profile for user {user.email}: {str(e)}")
                return Response(
                    {"message": f"An error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"Unexpected error in CreateServiceProviderView: {str(e)}")
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class EditServiceProviderView(APIView):
    """
    Edit an existing service provider profile.
    
    Allows users to update their service provider profile details.
    """
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Edit an existing service provider profile.
        
        Optional fields: company_name, company_address, company_description, 
                        company_phone_no, company_email, business_category, 
                        company_logo, opening_hour, closing_hour
        """
        try:
            user = get_user_from_token(request)

            try:
                service_provider = user.provider_profile
            except ServiceProvider.DoesNotExist:
                return Response(
                    {"message": "User does not have a business profile, kindly create one."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            company_name = request.data.get("company_name")
            company_address = request.data.get("company_address")
            company_description = request.data.get("company_description")
            company_phone_no = request.data.get("company_phone_no")
            company_email = request.data.get("company_email")
            business_category = request.data.get("business_category")
            company_logo = request.FILES.get("company_logo")
            opening_hour = request.data.get("opening_hour")
            closing_hour = request.data.get("closing_hour")

            if not any([company_name, company_address, company_description, company_phone_no, company_email, business_category, company_logo, opening_hour, closing_hour]):
                return Response(
                    {"message": "No data provided to update."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                if company_name:
                    service_provider.company_name = company_name
                if company_address:
                    service_provider.company_address = company_address
                if company_description:
                    service_provider.company_description = company_description
                if company_phone_no:
                    service_provider.company_phone_no = company_phone_no
                if company_email:
                    service_provider.company_email = company_email
                if business_category:
                    service_provider.business_category = business_category
                if company_logo:
                    logo_url = upload_to_cloudinary(company_logo)
                    service_provider.company_logo = logo_url
                if opening_hour:
                    service_provider.opening_hour = opening_hour
                if closing_hour:
                    service_provider.closing_hour = closing_hour

                service_provider.save()

                Notification.objects.create(
                    user=user,
                    title="Service Provider Profile Updated",
                    message="Your service provider profile has been updated successfully.",
                )

                logger.info(f"Service provider profile updated for user: {user.email}")
                return Response(
                    {"message": "Service provider profile updated successfully."},
                    status=status.HTTP_200_OK,
                )

            except IntegrityError:
                return Response(
                    {"message": "A service provider with this contact information already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Error updating service provider profile for user {user.email}: {str(e)}")
                return Response(
                    {"message": f"An error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"Unexpected error in EditServiceProviderView: {str(e)}")
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetServiceProviderDetailsView(APIView):
    """
    Get service provider profile details.
    
    Retrieves the service provider profile for the authenticated user.
    """
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get service provider profile details.
        """
        try:
            user = get_user_from_token(request)

            # Get the service provider profile
            try:
                service_provider = user.provider_profile
            except ServiceProvider.DoesNotExist:
                return Response(
                    {"message": "No service provider profile found."},
                    status=status.HTTP_200_OK,
                )

            # Serialize the service provider data
            data = {
                "company_name": service_provider.company_name,
                "company_address": service_provider.company_address,
                "company_description": service_provider.company_description,
                "company_phone_no": service_provider.company_phone_no,
                "company_email": service_provider.company_email,
                "business_category": service_provider.business_category,
                "company_logo": service_provider.company_logo,
                "opening_hour": service_provider.opening_hour,
                "closing_hour": service_provider.closing_hour,
                "is_approved": service_provider.is_approved,
                "created_at": service_provider.created_at,
            }

            logger.info(f"Service provider details retrieved for user: {user.email}")
            return Response(
                {"service_provider": data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrieving service provider details: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
