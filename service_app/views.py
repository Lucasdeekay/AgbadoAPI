from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.views import get_user_from_token
from notification_app.models import Notification
from provider_app.models import ServiceProvider
from provider_app.serializers import ServiceProviderSerializer
from service_app.models import ServiceRequest, ServiceRequestBid, SubService, Service, Booking
from service_app.serializers import BookingSerializer, ServiceRequestBidSerializer, ServiceRequestSerializer, ServiceSerializer, SubServiceSerializer


@method_decorator(csrf_exempt, name='dispatch')
class GetAllServicesDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        try:
            user = get_user_from_token(request)
            service_provider = user.provider_profile

            provider_data = {
                "user": service_provider.user.id,
                "company_name": service_provider.company_name,
                "company_address": service_provider.company_address,
                "company_description": service_provider.company_description,
                "company_phone_no": service_provider.company_phone_no,
                "company_email": service_provider.company_email,
                "business_category": service_provider.business_category,
                "company_logo": request.build_absolute_uri(service_provider.company_logo.url) if service_provider.company_logo else None,
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
                "image": request.build_absolute_uri(service.image.url) if service.image else None,
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

            return Response({
                "provider_details": provider_data,
                "services": services_data,
                "reviews": reviews_data
            }, status=status.HTTP_200_OK)

        except ServiceProvider.DoesNotExist:
            return Response({"message": "No service provider profile found."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class GetServiceDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, service_id):
        try:
            service = get_object_or_404(Service, id=service_id)

            service_data = {
                "id": service.id,
                "provider": service.provider.id,
                "name": service.name,
                "description": service.description,
                "image": request.build_absolute_uri(service.image.url) if service.image else None,
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
                "image": request.build_absolute_uri(subservice.image.url) if subservice.image else None,
                "is_active": subservice.is_active,
                "created_at": subservice.created_at,
            } for subservice in subservices]

            return Response({
                "service_details": service_data,
                "sub_services": subservices_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     

@method_decorator(csrf_exempt, name='dispatch')
class GetSubServiceDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, sub_service_id):
        try:
            subservice = get_object_or_404(SubService, id=sub_service_id)
            subservice_data = {
                "id": subservice.id,
                "service": subservice.service.id,
                "name": subservice.name,
                "description": subservice.description,
                "price": subservice.price,
                "image": request.build_absolute_uri(subservice.image.url) if subservice.image else None,
                "is_active": subservice.is_active,
                "created_at": subservice.created_at,
            }

            return Response({
                "sub_service": subservice_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class AddServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        try:
            # Get the service provider profile
            user = get_user_from_token(request)
        
            service_provider = ServiceProvider.objects.get(user=user)

            name = request.data.get('name')
            description = request.data.get('description')
            category = request.data.get('category')
            min_price = request.data.get('min_price')
            max_price = request.data.get('max_price')
            is_active = request.data.get('is_active', True) # Default to True if not provided
            image = request.FILES.get('image') # Handle image upload

            service = Service.objects.create(
                provider=service_provider,
                name=name,
                description=description,
                category=category,
                min_price=min_price,
                max_price=max_price,
                is_active=is_active,
                image=image, # Save the uploaded image
            )

            service_data = {
                'name': service.name,
                'description': service.description,
                'category': service.category,
                'min_price': str(service.min_price),
                'max_price': str(service.max_price),
                'is_active': service.is_active,
                'image': service.image.url if service.image else None,
                'created_at': service.created_at.isoformat(),
            }

            Notification.objects.create(
                user=user,
                title="New Service Added",
                message=f"You have added a new service: {service.name}"
            )

            return Response({"message": "Service added successfully.", "service": service_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class AddSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, service_id):
        try:
            user = get_user_from_token(request)

            service = get_object_or_404(Service, id=service_id)

            name = request.data.get('name')
            description = request.data.get('description')
            price = request.data.get('price')
            is_active = request.data.get('is_active', True)
            image = request.FILES.get('image')

            service = get_object_or_404(Service, id=service_id)
            subservice = SubService.objects.create(
                service=service,
                name=name,
                description=description,
                price=price,
                is_active=is_active,
                image=image,
            )

            subservice_data = {
                'name': subservice.name,
                'description': subservice.description,
                'price': str(subservice.price),
                'is_active': subservice.is_active,
                'image': subservice.image.url if subservice.image else None,
                'created_at': subservice.created_at.isoformat(),
            }

            Notification.objects.create(
                user=user,
                title="New Service Added",
                message=f"You have added a new service: {service.name}"
            )

            return Response({"message": "Subservice added successfully.", "subservice": subservice_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, service_id):
        try:
            user = get_user_from_token(request)

            service = get_object_or_404(Service, id=service_id)

            service.name = request.data.get('name', service.name)
            service.description = request.data.get('description', service.description)
            service.category = request.data.get('category', service.category)
            service.min_price = request.data.get('min_price', service.min_price)
            service.max_price = request.data.get('max_price', service.max_price)
            service.is_active = request.data.get('is_active', service.is_active)
            if 'image' in request.FILES:
                service.image = request.FILES['image']
            service.save()

            service_data = {
                'id': service.id,
                'provider': service.provider.id,
                'name': service.name,
                'description': service.description,
                'category': service.category,
                'min_price': str(service.min_price),
                'max_price': str(service.max_price),
                'is_active': service.is_active,
                'image': service.image.url if service.image else None,
                'created_at': service.created_at.isoformat(),
            }

            Notification.objects.create(
            user=user,
            title="Service Updated",
            message=f"You have updated the service: {service.name}"
        )

            return Response({"message": "Service updated successfully.", "service": service_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, subservice_id):
        try:
            user = get_user_from_token(request)

            subservice = get_object_or_404(SubService, id=subservice_id)

            subservice.service = get_object_or_404(Service, id=request.data.get('service'))
            subservice.name = request.data.get('name', subservice.name)
            subservice.description = request.data.get('description', subservice.description)
            subservice.price = request.data.get('price', subservice.price)
            subservice.is_active = request.data.get('is_active', subservice.is_active)
            if 'image' in request.FILES:
                subservice.image = request.FILES['image']
            subservice.save()

            subservice_data = {
                'id': subservice.id,
                'service': subservice.service.id,
                'name': subservice.name,
                'description': subservice.description,
                'price': str(subservice.price),
                'is_active': subservice.is_active,
                'image': subservice.image.url if subservice.image else None,
                'created_at': subservice.created_at.isoformat(),
            }

            Notification.objects.create(
            user=user,
            title="Subservice Updated",
            message=f"You have updated the subservice: {subservice.name}"
        )

            return Response({"message": "Subservice updated successfully.", "subservice": subservice_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class ServiceProviderBookingsView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        service_provider = get_user_from_token(request)  # Assuming the authenticated user is a service provider
        bookings = Booking.objects.filter(service_provider=service_provider)
        serializer = BookingSerializer(bookings, many=True)
        return Response({'bookings': serializer.data})
    
@method_decorator(csrf_exempt, name='dispatch')
class ServiceProviderBidsView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = get_user_from_token(request)

        try:
            service_provider = ServiceProvider.objects.get(user=user)
        except ServiceProvider.DoesNotExist:
            return Response({"message": "Service provider profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get service requests in the same category as the service provider
        service_requests = ServiceRequest.objects.filter(category=service_provider.business_category).exclude(user=user)
        request_serializer = ServiceRequestSerializer(service_requests, many=True, context={'request': request})

        # Get bids made by this service provider, excluding bids from the current user.
        bids = ServiceRequestBid.objects.filter(service_provider=user)

        bid_serializer = ServiceRequestBidSerializer(bids, many=True, context={'request': request})

        return Response({
            'requests': request_serializer.data,
            'bids': bid_serializer.data,
        })

@method_decorator(csrf_exempt, name='dispatch')
class SubmitBidView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, service_request_id, *args, **kwargs):
        service_provider = get_user_from_token(request)
        try:
            service_request = ServiceRequest.objects.get(id=int(service_request_id))
        except ServiceRequest.DoesNotExist:
            raise NotFound("Service request not found")

        price = request.data.get('price')

        if price is None:
            return Response({"message": "Price is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            price = float(price)  # Convert price to float
        except ValueError:
            return Response({"message": "Invalid price format"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a bid already exists
        existing_bid = ServiceRequestBid.objects.filter(service_request=service_request, service_provider=service_provider).first()

        if existing_bid:
            # Update existing bid
            existing_bid.price = price
            existing_bid.save()

            Notification.objects.create(
                user=service_provider,
                title="Bid Updated",
                message=f"You have updated your bid for service request: {service_request.title}"
            )

            return Response({"message": "Bid updated successfully"}, status=status.HTTP_200_OK)
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

            return Response({"message": "Bid submitted successfully"}, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class CancelBookingView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
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
        
        return Response({"message": "Booking cancelled successfully"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class CompleteBookingView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
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
        
        return Response({"message": "Booking completed successfully"}, status=status.HTTP_200_OK)
