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
from service_app.models import Category, ServiceRequest, ServiceRequestBid, SubService, Service, Booking
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
    permission_classes = [IsAuthenticated]

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
                "business_category": service_provider.business_category.name,
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
                "category": service.category.name,
                "min_price": service.min_price,
                "max_price": service.max_price,
                "is_active": service.is_active,
                "created_at": service.created_at,
            } for service in services]

            bookings = Booking.objects.filter(provider=service_provider).exclude(feedback=None)
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
    permission_classes = [IsAuthenticated]

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
                "category": service.category.name,
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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

            category, _ = Category.objects.get_or_create(name=category)

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
                'category': service.category.name,
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
                service.image = upload_to_cloudinary(request.FILES['image'], old_image=service.image)

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
    permission_classes = [IsAuthenticated]

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
                subservice.image = upload_to_cloudinary(request.FILES['image'], old_image=subservice.image)

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
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)
            bookings = Booking.objects.filter(provider=provider)
            serializer = BookingSerializer(bookings, many=True)

            logger.info(f"Retrieved {len(bookings)} bookings for provider: {provider}")
            return Response({'bookings': serializer.data})

        except Exception as e:
            logger.error(f"Error retrieving provider bookings: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class ServiceProviderBidsView(APIView):
    """
    Get service requests in provider's category and their bids.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = get_user_from_token(request)

            try:
                provider = ServiceProvider.objects.get(user=user)
            except ServiceProvider.DoesNotExist:
                return Response(
                    {"message": "User does not have a business profile, kindly create one."},
                    status=status.HTTP_404_NOT_FOUND
                )

            service_requests = ServiceRequest.objects.filter(
                category=provider.business_category
            ).exclude(user=user)

            request_serializer = ServiceRequestSerializer(
                service_requests, many=True, context={'request': request}
            )

            bids = ServiceRequestBid.objects.filter(provider=provider)
            bid_data = [{
                'id': bid.id,
                'service_request': ServiceRequestSerializer(bid.service_request).data,
                'amount': str(bid.amount),
                'proposal': bid.proposal,
                'status': bid.status,
                'latitude': bid.latitude,
                'longitude': bid.longitude,
                'address': bid.address,
                'distance': bid.calculate_distance_km(),
                'created_at': bid.created_at.isoformat(),
            } for bid in bids]

            logger.info(f"Retrieved {len(service_requests)} requests & {len(bids)} bids for provider: {provider.company_name}")
            return Response({
                'requests': request_serializer.data,
                'bids': bid_data,
            })

        except Exception as e:
            logger.error(f"Error retrieving provider requests/bids: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SubmitBidView(APIView):
    """
    Submit or update a bid for a service request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, service_request_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)

            try:
                service_request = ServiceRequest.objects.get(id=int(service_request_id))
            except ServiceRequest.DoesNotExist:
                raise NotFound("Service request not found")

            amount = request.data.get('amount')
            proposal = request.data.get('proposal')
            laitude = request.data.get('laitude')
            longitude = request.data.get('longitude')
            address = request.data.get('address')

            if not amount:
                return Response({"message": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                amount = float(amount)
            except ValueError:
                return Response({"message": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)

            existing_bid = ServiceRequestBid.objects.filter(
                service_request=service_request,
                provider=provider
            ).first()

            if existing_bid:
                existing_bid.amount = amount
                existing_bid.proposal = proposal or existing_bid.proposal
                existing_bid.latitude = laitude or existing_bid.latitude
                existing_bid.longitude = longitude or existing_bid.longitude
                existing_bid.address = address or existing_bid.address
                existing_bid.save()

                Notification.objects.create(
                    user=service_request.user,
                    title="Bid Updated",
                    message=f"{provider.user.email} updated their bid on your request: {service_request.title}"
                )

                logger.info(f"Bid updated for request {service_request.title}")
                return Response({"message": "Bid updated successfully"}, status=status.HTTP_200_OK)

            else:
                ServiceRequestBid.objects.create(
                    service_request=service_request,
                    provider=provider,
                    amount=amount,
                    proposal=proposal
                )

                Notification.objects.create(
                    user=service_request.user,
                    title="New Bid Submitted",
                    message=f"{provider.user.email} submitted a bid on your request: {service_request.title}"
                )

                logger.info(f"Bid submitted for request {service_request.title}")
                return Response({"message": "Bid submitted successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error submitting bid: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WithdrawBidView(APIView):
    """
    Withdraw a bid -> Withdraw a bid made for a request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, bid_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)

            try:
                bid = ServiceRequestBid.objects.get(id=bid_id, provider=provider)
            except ServiceRequestBid.DoesNotExist:
                raise NotFound("Bid not found or not yours to accept")


            # Accept the chosen bid
            bid.status = "Withdrawn"
            bid.save()

            Notification.objects.create(
                user=bid.provider.user,
                title="Bid Withdrawn",
                message=f"Your bid for {bid.service_request.title} was withdrawn!"
            )

            logger.info(f"Bid {bid.id} for Service Request has {bid.service_request.id} has been withdrawn")
            return Response(
                {"message": "Bid withdrawn successfully"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error withdrawing bid: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class InProgressBookingView(APIView):
    """
    Set a booking in progress by the provider.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)

            try:
                booking = Booking.objects.get(id=int(booking_id), provider=provider)
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")

            booking.status = 'In Progress'
            booking.save()

            Notification.objects.create(
                user=booking.user,
                title="Booking In Progress",
                message=f"Your booking for {booking.bid.service_request.title} was set in progress."
            )

            logger.info(f"Booking {booking.id} in progress by provider {provider}")
            return Response({"message": "Booking in progress successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error setting booking in progress: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelBookingView(APIView):
    """
    Cancel a booking by the provider.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)

            try:
                booking = Booking.objects.get(id=int(booking_id))
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")

            booking.status = 'Cancelled'
            booking.save()

            Notification.objects.create(
                user=booking.user,
                title="Booking Cancelled",
                message=f"Your booking for {booking.bid.service_request.title} was cancelled."
            )

            logger.info(f"Booking {booking.id} cancelled by provider {provider}")
            return Response({"message": "Booking cancelled successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error cancelling booking: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompleteBookingView(APIView):
    """
    Mark a booking as completed by the provider.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            provider = ServiceProvider.objects.get(user=user)

            try:
                booking = Booking.objects.get(id=int(booking_id), provider=provider)
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")

            booking.status = 'Completed'
            booking.save()

            Notification.objects.create(
                user=booking.user,
                title="Booking Completed",
                message=f"Your booking for {booking.bid.service_request.title} has been marked as completed."
            )

            logger.info(f"Booking {booking.id} marked completed by provider {provider}")
            return Response({"message": "Booking marked as completed"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error completing booking: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ConfirmBookingView(APIView):
    """
    Mark a booking as confirmed by the user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)

            try:
                booking = Booking.objects.get(id=int(booking_id), user=user)
            except Booking.DoesNotExist:
                raise NotFound("Booking not found")

            booking.status = 'Confirmed'
            booking.save()

            Notification.objects.create(
                user=booking.provider.user,
                title="Booking Confirmed",
                message=f"Your booking for {booking.bid.service_request.title} has been marked as confirmed."
            )
            print("Saved")

            logger.info(f"Booking {booking.id} marked confirmed by provider {user.email}")
            return Response({"message": "Booking marked as confirmed"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error confirming booking: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserBookingsView(APIView):
    """
    Get all bookings for a user (client).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = get_user_from_token(request)
            bookings = Booking.objects.filter(user=user)
            serializer = BookingSerializer(bookings, many=True)

            logger.info(f"Retrieved {len(bookings)} bookings for user: {user.email}")
            return Response({'bookings': serializer.data})

        except Exception as e:
            logger.error(f"Error retrieving user bookings: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AcceptBidView(APIView):
    """
    Accept a bid -> Creates a booking & rejects all other bids for the same request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, bid_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)

            try:
                bid = ServiceRequestBid.objects.get(id=bid_id, service_request__user=user)
            except ServiceRequestBid.DoesNotExist:
                raise NotFound("Bid not found or not yours to accept")
            
            # Update service request status
            request = bid.service_request
            request.status = "Awarded"
            request.save()

            # Reject all other bids for this service request
            other_bids = ServiceRequestBid.objects.filter(
                service_request=bid.service_request
            ).exclude(id=bid.id)

            for other in other_bids:
                other.status = "Rejected"
                other.save()

                Notification.objects.create(
                    user=other.provider,
                    title="Bid Rejected",
                    message=f"Your bid for {other.service_request.title} was rejected."
                )

            # Accept the chosen bid
            bid.status = "Accepted"
            bid.save()

            # Create booking
            booking = Booking.objects.create(
                user=user,
                provider=bid.provider,
                bid=bid,
                amount=bid.amount,
                status="Pending"
            )

            Notification.objects.create(
                user=ServiceProvider.objects.get(id=bid.provider.id).user,
                title="Bid Accepted",
                message=f"Your bid for {bid.service_request.title} was accepted!"
            )

            logger.info(f"Booking {booking.id} created by {user.email} from bid {bid.id}")
            return Response(
                {"message": "Bid accepted, booking created, and other bids rejected"},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error accepting bid: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeclineBidView(APIView):
    """
    Decline a specific bid without accepting any other.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, bid_id, *args, **kwargs):
        try:
            user = get_user_from_token(request)

            try:
                bid = ServiceRequestBid.objects.get(id=bid_id, service_request__user=user)
            except ServiceRequestBid.DoesNotExist:
                raise NotFound("Bid not found or not yours to decline")

            bid.status = "Rejected"
            bid.save()

            Notification.objects.create(
                user=ServiceProvider.objects.get(id=bid.provider.id).user,
                title="Bid Rejected",
                message=f"Your bid for {bid.service_request.title} was declined."
            )

            logger.info(f"Bid {bid.id} declined by user {user.email}")
            return Response(
                {"message": "Bid declined successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error declining bid: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateServiceRequestView(APIView):
    """
    Create a service request.
    
    Allows user to create new service request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a service request.
        
        Required fields: title, description, category, price
        Optional fields: longitude, latitude, address
        """
        try:
            user = get_user_from_token(request)

            title = request.data.get('title')
            description = request.data.get('description')
            category = request.data.get('category')
            price = request.data.get('price')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            address = request.data.get('address')
            image = request.FILES.get('image')

            if image:
                image_url = upload_to_cloudinary(image)
            else:
                image_url = None

            category, _ = Category.objects.get_or_create(name=category)

            service_request = ServiceRequest.objects.create(
                user=user,
                title=title,
                description=description,
                category=category,
                price=price,
                latitude=latitude,
                longitude=longitude,
                address=address,
                image=image_url,
            )

            Notification.objects.create(
                user=user,
                title="New Service Request Added",
                message=f"You have added a new service request: {service_request.title}"
            )

            service_request_data = {
                'id': service_request.id,
                'title': service_request.title,
                'description': service_request.description,
                'category': service_request.category.name,
                'price': str(service_request.price),
                'status': service_request.status,
                'latitude': service_request.latitude,
                'longitude': service_request.longitude,
                'address': service_request.address,
                'image': service_request.image,
                'created_at': service_request.created_at.isoformat(),
            }
            
            logger.info(f"Service Request added successfully: {service_request.title}")
            return Response(
                {"message": "Service Request added successfully.", "service":service_request_data}, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error adding service request: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class EditServiceRequestView(APIView):
    """
    Create a service request.
    
    Allows user to create new service request.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, service_request_id, *args, **kwargs):
        """
        Create a service request.
        
        Required fields: title, description, category, price
        Optional fields: longitude, latitude, address
        """
        try:
            user = get_user_from_token(request)

            title = request.data.get('title')
            description = request.data.get('description')
            category = request.data.get('category')
            price = request.data.get('price')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            address = request.data.get('address')
            image = request.FILES.get('image', None)

            service_request = ServiceRequest.objects.get(id=service_request_id)
            
            if title:
                service_request.title = title
            if description:
                service_request.description = description
            if category:
                category, _ = Category.objects.get_or_create(name=category)
                service_request.category = category
            if price:
                service_request.price = price
            if latitude:
                service_request.latitude = latitude
            if longitude:
                service_request.longitude = longitude
            if address:
                service_request.address = address
            if image_url:
                image_url = upload_to_cloudinary(image, old_image=service_request.image)
                service_request.image = image_url
            else:
                image_url = None

            Notification.objects.create(
                user=user,
                title="Service Request Updated",
                message=f"You have update a service request: {service_request.title}"
            )

            service_request_data = {
                'id': service_request.id,
                'title': service_request.title,
                'description': service_request.description,
                'category': service_request.category.name,
                'price': str(service_request.price),
                'status': service_request.status,
                'latitude': service_request.latitude,
                'longitude': service_request.longitude,
                'address': service_request.address,
                'image': service_request.image,
                'created_at': service_request.created_at.isoformat(),
            }
            
            logger.info(f"Service Request updated successfully: {service_request.title}")
            return Response(
                {"message": "Service Request updated successfully.", "service":service_request_data}, 
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error updating service request: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class GetUserServiceRequestsView(APIView):
    """
    Get all service requests made by a user.
    
    Retrieves comprehensive information about the user's service requests.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all service requests made by a user.
        """
        try:
            user = get_user_from_token(request)

            service_requests = ServiceRequest.objects.filter(user=user)
            service_request_data = [{
                'id': request.id,
                'title': request.title,
                'description': request.description,
                'category': request.category.name,
                'price': str(request.price),
                'status': request.status,
                'latitude': request.latitude,
                'longitude': request.longitude,
                'address': request.address,
                'image': request.image,
                'created_at': request.created_at.isoformat(),
            } for request in service_requests]

            
            logger.info(f"Retrieved service requests for user: {user}")
            return Response({
                "service_requests": service_request_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving services requests: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetServiceRequestBidsView(APIView):
    """
    Get all bids for a service request.
    
    Retrieves comprehensive information about the service request's bids.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, service_request_id, *args, **kwargs):
        """
        Get all bids for a service request.
        """
        try:
            user = get_user_from_token(request)

            service_request = ServiceRequest.objects.get(id=service_request_id)
            bids = ServiceRequestBid.objects.filter(service_request=service_request)
            bid_data = [{
                'id': bid.id,
                'service_request': ServiceRequestSerializer(bid.service_request).data,
                'amount': str(bid.amount),
                'proposal': bid.proposal,
                'status': bid.status,
                'latitude': bid.latitude,
                'longitude': bid.longitude,
                'address': bid.address,
                'distance': bid.calculate_distance_km(),
                'created_at': bid.created_at.isoformat(),
            } for bid in bids]

            
            logger.info(f"Retrieved service request bids for user: {user}")
            return Response({
                "bids": bid_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving services request bids: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GetServiceRequestDetailsView(APIView):
    """
    Get details of a specific service request.
    
    Retrieves service request information.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, service_request_id):
        """
        Get details of a specific service request.
        
        URL parameter: service_request_id
        """
        try:
            service_request = get_object_or_404(SubService, id=service_request_id)
            service_request_data = {
                "id": service_request.id,
                "title": service_request.title,
                "description": service_request.description,
                "price": service_request.price,
                "category": service_request.category.name,
                "status": service_request.status,
                "image": service_request.image,
                "address": service_request.image,
                "bid_count": service_request.get_bids_count(),
                "created_at": service_request.created_at,
            }

            logger.info(f"Retrieved service request details for service request ID: {service_request_id}")
            return Response({
                "service_request": service_request_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error retrieving service request details for service request ID {service_request_id}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
