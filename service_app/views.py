"""
Service app views for handling service-related operations.

This module contains views for managing services, subservices, bookings, and bids
with proper error handling and logging.
"""

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from auth_app.utils import upload_to_cloudinary
from auth_app.views import get_user_from_token
from notification_app.models import Notification
from provider_app.models import ServiceProvider
from provider_app.serializers import ServiceProviderSerializer
from service_app.models import ServiceRequest, ServiceRequestBid, SubService, Service, Booking
from service_app.serializers import BookingSerializer, ServiceRequestBidSerializer, ServiceRequestSerializer, ServiceSerializer, SubServiceSerializer

import logging

logger = logging.getLogger(__name__)



class GetAllServicesDetailsView(APIView):
    """
    Get all services and details for a service provider.
    
    Retrieves comprehensive information about the service provider's services,
    reviews, and provider details.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def get(self, request):
        """
        Get all services and details for a service provider.
        """
        try:
            user = get_user_from_token(request)
            service_provider = ServiceProvider.objects.get(user=user)

            provider_data = {
                "user": service_provider.user.id,
                "company_name": service_provider.company_name,
                "company_address": service_provider.company_address,
                "company_description": service_provider.company_description,
                "company_phone_no": service_provider.company_phone_no,
                "company_email": service_provider.company_email,
                "business_category": service_provider.business_category,
                "company_logo": service_provider.company_logo,
                "opening_hour": service_provider.opening_hour,
                "closing_hour": service_provider.closing_hour,
                "avg_rating": service_provider.avg_rating,
                "rating_population": service_provider.rating_population,
                "is_approved": service_provider.is_approved,
                "created_at": service_provider.created_at,
            }

            services = Service.objects.filter(provider=service_provider)
            services_data = [{
                "id": service.id,
                "provider": service.provider.id,
                "name": service.name,
                "description": service.description,
                "image": service.image,
                "category": service.category,
                "min_price": service.min_price,
                "max_price": service.max_price,
                "is_active": service.is_active,
                "created_at": service.created_at,
            } for service in services]

            bookings = Booking.objects.filter(service_provider=service_provider.user).exclude(feedback=None)
            reviews_data = [{
                "user__email": booking.user.email,
                "feedback": booking.feedback,
                "rating": booking.rating,
                "created_at": booking.created_at,
            } for booking in bookings]

            logger.info(f"Retrieved services details for provider: {service_provider.company_name}")
            return Response({
                "provider_details": provider_data,
                "services": services_data,
                "reviews": reviews_data
            }, status=status.HTTP_200_OK)

        except ServiceProvider.DoesNotExist:
            return Response(
                {"message": "User does not have a business profile, kindly create one."}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error retrieving services details: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class GetServiceDetailsView(APIView):
    """
    Get details of a specific service.
    
    Retrieves service information and its associated subservices.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def get(self, request, service_id):
        """
        Get details of a specific service.
        
        URL parameter: service_id
        """
        try:
            service = get_object_or_404(Service, id=service_id)

            service_data = {
                "id": service.id,
                "provider": service.provider.id,
                "name": service.name,
                "description": service.description,
                "image": service.image,
                "category": service.category,
                "min_price": service.min_price,
                "max_price": service.max_price,
                "is_active": service.is_active,
                "created_at": service.created_at,
            }

            subservices = SubService.objects.filter(service=service)
            subservices_data = [{
                "id": subservice.id,
                "service": subservice.service.id,
                "name": subservice.name,
                "description": subservice.description,
                "price": subservice.price,
                "image": subservice.image,
                "is_active": subservice.is_active,
                "created_at": subservice.created_at,
            } for subservice in subservices]

            logger.info(f"Retrieved service details for service ID: {service_id}")
            return Response({
                "service_details": service_data,
                "sub_services": subservices_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving service details for service ID {service_id}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class GetSubServiceDetailsView(APIView):
    """
    Get details of a specific subservice.
    
    Retrieves subservice information.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def get(self, request, sub_service_id):
        """
        Get details of a specific subservice.
        
        URL parameter: sub_service_id
        """
        try:
            subservice = get_object_or_404(SubService, id=sub_service_id)
            subservice_data = {
                "id": subservice.id,
                "service": subservice.service.id,
                "name": subservice.name,
                "description": subservice.description,
                "price": subservice.price,
                "image": subservice.image,
                "is_active": subservice.is_active,
                "created_at": subservice.created_at,
            }

            logger.info(f"Retrieved subservice details for subservice ID: {sub_service_id}")
            return Response({
                "sub_service": subservice_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving subservice details for subservice ID {sub_service_id}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AddServiceView(APIView):
    """
    Add a new service.
    
    Allows service providers to create new services.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def post(self, request):
        """
        Add a new service.
        
        Required fields: name, description, category, min_price, max_price
        Optional fields: is_active, image
        """
        try:
            user = get_user_from_token(request)
            service_provider = ServiceProvider.objects.get(user=user)

            name = request.data.get('name')
            description = request.data.get('description')
            category = request.data.get('category')
            min_price = request.data.get('min_price')
            max_price = request.data.get('max_price')
            is_active = request.data.get('is_active', True)
            image = request.FILES.get('image')

            if image:
                image_url = upload_to_cloudinary(image)
            else:
                image_url = None

            service = Service.objects.create(
                provider=service_provider,
                name=name,
                description=description,
                category=category,
                min_price=min_price,
                max_price=max_price,
                is_active=is_active,
                image=image_url,
            )

            Notification.objects.create(
                user=user,
                title="New Service Added",
                message=f"You have added a new service: {service.name}"
            )

            service_data = {
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'category': service.category,
                'min_price': str(service.min_price),
                'max_price': str(service.max_price),
                'is_active': service.is_active,
                'image': service.image,
                'created_at': service.created_at.isoformat(),
            }
            
            logger.info(f"Service added successfully: {service.name} by provider: {service_provider.company_name}")
            return Response(
                {"message": "Service added successfully.", "service": service_data}, 
                status=status.HTTP_201_CREATED
            )

        except ServiceProvider.DoesNotExist:
            return Response(
                {"message": "User does not have a business profile."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error adding service: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AddSubServiceView(APIView):
    """
    Add a new subservice.
    
    Allows service providers to create new subservices for existing services.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def post(self, request, service_id):
        """
        Add a new subservice.
        
        URL parameter: service_id
        Required fields: name, description, price
        Optional fields: is_active, image
        """
        try:
            user = get_user_from_token(request)
            service = get_object_or_404(Service, id=service_id)

            name = request.data.get('name')
            description = request.data.get('description')
            price = request.data.get('price')
            is_active = request.data.get('is_active', True)
            image = request.FILES.get('image')

            image_url = upload_to_cloudinary(image) if image else None

            subservice = SubService.objects.create(
                service=service,
                name=name,
                description=description,
                price=price,
                is_active=is_active,
                image=image_url,
            )

            Notification.objects.create(
                user=user,
                title="New Subservice Added",
                message=f"You have added a new subservice: {subservice.name}"
            )

            subservice_data = {
                'id': subservice.id,
                'name': subservice.name,
                'description': subservice.description,
                'price': str(subservice.price),
                'is_active': subservice.is_active,
                'image': subservice.image,
                'created_at': subservice.created_at.isoformat(),
            }
            
            logger.info(f"Subservice added successfully: {subservice.name} for service: {service.name}")
            return Response(
                {"message": "Subservice added successfully.", "subservice": subservice_data}, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error adding subservice: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class EditServiceView(APIView):
    """
    Edit an existing service.
    
    Allows service providers to update their services.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def post(self, request, service_id):
        """
        Edit an existing service.
        
        URL parameter: service_id
        Optional fields: name, description, category, min_price, max_price, is_active, image
        """
        try:
            user = get_user_from_token(request)
            service = get_object_or_404(Service, id=service_id)

            if 'image' in request.FILES:
                service.image = upload_to_cloudinary(request.FILES['image'])

            for field in ['name', 'description', 'category', 'min_price', 'max_price', 'is_active']:
                if field in request.data:
                    setattr(service, field, request.data.get(field))

            service.save()

            Notification.objects.create(
                user=user,
                title="Service Updated",
                message=f"You have updated the service: {service.name}"
            )

            service_data = ServiceSerializer(service, context={'request': request}).data
            
            logger.info(f"Service updated successfully: {service.name}")
            return Response(
                {"message": "Service updated successfully.", "service": service_data}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error updating service: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class EditSubServiceView(APIView):
    """
    Edit an existing subservice.
    
    Allows service providers to update their subservices.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes  = [IsAuthenticated]

    def post(self, request, subservice_id):
        """
        Edit an existing subservice.
        
        URL parameter: subservice_id
        Optional fields: name, description, price, is_active, image
        """
        try:
            user = get_user_from_token(request)
            subservice = get_object_or_404(SubService, id=subservice_id)

            if 'image' in request.FILES:
                subservice.image = upload_to_cloudinary(request.FILES['image'])

            for field in ['name', 'description', 'price', 'is_active', 'service']:
                if field in request.data:
                    setattr(subservice, field, request.data.get(field))

            subservice.save()

            Notification.objects.create(
                user=user,
                title="Subservice Updated",
                message=f"You have updated the subservice: {subservice.name}"
            )

            subservice_data = SubServiceSerializer(subservice, context={'request': request}).data
            
            logger.info(f"Subservice updated successfully: {subservice.name}")
            return Response(
                {"message": "Subservice updated successfully.", "subservice": subservice_data}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error updating subservice: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ServiceProviderBookingsView(APIView):
    """
    Get all bookings for a service provider.
    
    Retrieves all bookings associated with the service provider.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        service_provider = get_user_from_token(request)  # Assuming the authenticated user is a service provider
        bookings = Booking.objects.filter(service_provider=service_provider)
        serializer = BookingSerializer(bookings, many=True)
        return Response({'bookings': serializer.data})
    

        """
        Get all bookings for a service provider.
        """
        try:
            service_provider = get_user_from_token(request)
            bookings = Booking.objects.filter(service_provider=service_provider)
            serializer = BookingSerializer(bookings, many=True)
            
            logger.info(f"Retrieved {len(bookings)} bookings for service provider: {service_provider.email}")
            return Response({'bookings': serializer.data})
            
        except Exception as e:
            logger.error(f"Error retrieving bookings: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ServiceProviderBidsView(APIView):
    """
    Get service requests and bids for a service provider.
    
    Retrieves service requests in the provider's category and their bids.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get service requests and bids for a service provider.
        """
        try:
            user = get_user_from_token(request)

            try:
                service_provider = ServiceProvider.objects.get(user=user)
            except ServiceProvider.DoesNotExist:
                return Response(
                    {"message": "User does not have a business profile, kindly create one."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get service requests in the same category as the service provider
            service_requests = ServiceRequest.objects.filter(category=service_provider.business_category).exclude(user=user)
            request_serializer = ServiceRequestSerializer(service_requests, many=True, context={'request': request})

            # Get bids made by this service provider
            bids = ServiceRequestBid.objects.filter(service_provider=user)
            bid_serializer = ServiceRequestBidSerializer(bids, many=True, context={'request': request})

            logger.info(f"Retrieved {len(service_requests)} service requests and {len(bids)} bids for provider: {service_provider.company_name}")
            return Response({
                'requests': request_serializer.data,
                'bids': bid_serializer.data,
            })
            
        except Exception as e:
            logger.error(f"Error retrieving service requests and bids: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class SubmitBidView(APIView):
    """
    Submit a bid for a service request.
    
    Allows service providers to submit or update bids for service requests.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, service_request_id, *args, **kwargs):
        """
        Submit a bid for a service request.
        
        URL parameter: service_request_id
        Required fields: price
        """
        try:
            service_provider = get_user_from_token(request)
            try:
                service_request = ServiceRequest.objects.get(id=int(service_request_id))
            except ServiceRequest.DoesNotExist:
                raise NotFound("Service request not found")

            price = request.data.get('price')

            if price is None:
                return Response(
                    {"message": "Price is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                price = float(price)
            except ValueError:
                return Response(
                    {"message": "Invalid price format"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if a bid already exists
            existing_bid = ServiceRequestBid.objects.filter(
                service_request=service_request, 
                service_provider=service_provider
            ).first()

            if existing_bid:
                # Update existing bid
                existing_bid.price = price
                existing_bid.save()

                Notification.objects.create(
                    user=service_provider,
                    title="Bid Updated",
                    message=f"You have updated your bid for service request: {service_request.title}"
                )

                logger.info(f"Bid updated for service request: {service_request.title}")
                return Response(
                    {"message": "Bid updated successfully"}, 
                    status=status.HTTP_200_OK
                )
            else:
                # Create new bid
                ServiceRequestBid.objects.create(
                    service_request=service_request,
                    service_provider=service_provider,
                    price=price
                )

                Notification.objects.create(
                    user=service_provider,
                    title="Bid Submitted",
                    message=f"You have submitted a bid for service request: {service_request.title}"
                )

                logger.info(f"Bid submitted for service request: {service_request.title}")
                return Response(
                    {"message": "Bid submitted successfully"}, 
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            logger.error(f"Error submitting bid: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CancelBookingView(APIView):
    """
    Cancel a booking.
    
    Allows service providers to cancel bookings.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
        """
        Cancel a booking.
        
        URL parameter: booking_id
        """
        try:
            service_provider = get_user_from_token(request)
            try:
                booking = Booking.objects.get(id=int(booking_id), service_provider=service_provider)
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")
            
            booking.provider_status = 'Cancelled'
            booking.save()

            Notification.objects.create(
                user=service_provider,
                title="Booking Cancelled",
                message=f"You have cancelled booking: {booking.service_request.title}"
            )
            
            logger.info(f"Booking cancelled: {booking.service_request.title}")
            return Response(
                {"message": "Booking cancelled successfully"}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error cancelling booking: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CompleteBookingView(APIView):
    """
    Complete a booking.
    
    Allows service providers to mark bookings as completed.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
        """
        Complete a booking.
        
        URL parameter: booking_id
        """
        try:
            service_provider = get_user_from_token(request)
            try:
                booking = Booking.objects.get(id=int(booking_id), service_provider=service_provider)
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")
            
            booking.provider_status = 'Completed'
            booking.save()

            Notification.objects.create(
                user=service_provider,
                title="Booking Completed",
                message=f"You have completed booking: {booking.service_request.title}"
            )
            
            logger.info(f"Booking completed: {booking.service_request.title}")
            return Response(
                {"message": "Booking completed successfully"}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error completing booking: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
