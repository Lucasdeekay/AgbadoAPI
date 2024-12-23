from django.db import IntegrityError
from requests import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from auth_app.views import get_user_from_token
from provider_app.models import ServiceProvider


class CreateServiceProviderView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_token(request)

        # Check if the user already has a provider profile
        if hasattr(user, "provider_profile"):
            return Response(
                {"error": "User already has a provider profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract data from the request
        company_name = request.data.get("company_name")
        company_address = request.data.get("company_address")
        contact_info = request.data.get("contact_info")
        business_category = request.data.get("business_category")
        company_logo = request.FILES.get("company_logo")

        # Validate required fields
        if not company_name or not company_address or not contact_info or not business_category:
            return Response(
                {"error": "All required fields must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create the service provider profile
            service_provider = ServiceProvider.objects.create(
                user=user,
                company_name=company_name,
                company_address=company_address,
                contact_info=contact_info,
                business_category=business_category,
                company_logo=company_logo,
            )

            service_provider.save()

            return Response(
                {"message": "Service provider profile created successfully."},
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError:
            return Response(
                {"error": "A service provider with this contact information already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class EditServiceProviderView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = get_user_from_token(request)

        # Get the service provider profile
        try:
            service_provider = user.provider_profile
        except ServiceProvider.DoesNotExist:
            return Response(
                {"error": "Service provider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Extract data from the request
        company_name = request.data.get("company_name")
        company_address = request.data.get("company_address")
        contact_info = request.data.get("contact_info")
        business_category = request.data.get("business_category")
        company_logo = request.FILES.get("company_logo")

        # Handle empty requests gracefully
        if not company_name and not company_address and not contact_info and not business_category and not company_logo:
            return Response(
                {"error": "No data provided to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Update fields if they are provided
            if company_name:
                service_provider.company_name = company_name
            if company_address:
                service_provider.company_address = company_address
            if contact_info:
                service_provider.contact_info = contact_info
            if business_category:
                service_provider.business_category = business_category
            if company_logo:
                service_provider.company_logo = company_logo

            service_provider.save()

            return Response(
                {"message": "Service provider profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        except IntegrityError:
            return Response(
                {"error": "A service provider with this contact information already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class GetServiceProviderDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_token(request)

        # Get the service provider profile
        try:
            service_provider = user.provider_profile
        except ServiceProvider.DoesNotExist:
            return Response(
                {"message": "No service provider profile found."},
                status=status.HTTP_200_OK,  # Return success with an empty response
            )

        # Serialize the service provider data
        data = {
            "company_name": service_provider.company_name,
            "company_address": service_provider.company_address,
            "contact_info": service_provider.contact_info,
            "business_category": service_provider.business_category,
            "company_logo": service_provider.company_logo.url if service_provider.company_logo else None,
            "is_approved": service_provider.is_approved,
            "created_at": service_provider.created_at,
        }

        return Response(
            {"service_provider": data},
            status=status.HTTP_200_OK,
        )
