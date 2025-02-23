from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.views import get_user_from_token
from provider_app.models import ServiceProvider
from provider_app.serializers import ServiceProviderSerializer
from service_app.models import ServiceRequest, ServiceRequestBid, SubService, Service, Booking
from service_app.serializers import BookingSerializer, ServiceRequestBidSerializer, ServiceSerializer, SubServiceSerializer

@method_decorator(csrf_exempt, name='dispatch')
class GetAllServicesDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the service provider profile
        try:
            user = get_user_from_token(request)
            service_provider = user.provider_profile
        except ServiceProvider.DoesNotExist:
            return Response(
                {"message": "No service provider profile found."},
                status=status.HTTP_200_OK,  # Return success with an empty response
            )
        
            
        # Fetch service provider details
        service_provider = ServiceProvider.objects.get(user=user)
        provider_data = ServiceProviderSerializer(service_provider).data

        # Fetch services provided by the service provider
        services = Service.objects.filter(provider=service_provider)
        services_data = ServiceSerializer(services, many=True).data

        # Fetch reviews from the Booking model
        bookings = Booking.objects.filter(service_provider=service_provider.user).exclude(feedback=None)
        reviews_data = bookings.values(
            'user__email',  # Reviewer email
            'feedback',  # Review text
            'rating',  # Review rating
            'created_at'  # Date of review
        )

        return Response({
            "provider_details": provider_data,
            "services": services_data,
            "reviews": reviews_data
        }, status=status.HTTP_200_OK)

        
@method_decorator(csrf_exempt, name='dispatch')
class ServiceDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def get(self, request, service_id):
        try:

            # Fetch service details
            service = get_object_or_404(Service, id=service_id)
            service_data = ServiceSerializer(service).data

            # Fetch subservices for the service
            subservices = SubService.objects.filter(service=service)
            subservices_data = SubServiceSerializer(subservices, many=True).data

            return Response({
                "service_details": service_data,
                "sub_services": subservices_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

            return Response({"message": "Service added successfully.", "service": service_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class AddSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, service_id):
        try:
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

            return Response({"message": "Subservice added successfully.", "subservice": subservice_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, service_id):
        try:
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

            return Response({"message": "Service updated successfully.", "service": service_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, subservice_id):
        try:
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

            return Response({"message": "Subservice updated successfully.", "subservice": subservice_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        service_provider = get_user_from_token(request)  # Assuming the authenticated user is a service provider
        bids = ServiceRequestBid.objects.filter(service_provider=service_provider)
        serializer = ServiceRequestBidSerializer(bids, many=True)
        return Response({'requests': serializer.data})

@method_decorator(csrf_exempt, name='dispatch')
class SubmitBidView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, service_request_id, *args, **kwargs):
        service_provider = get_user_from_token(request)
        try:
            service_request = ServiceRequest.objects.get(id=service_request_id)
        except ServiceRequest.DoesNotExist:
            raise NotFound("Service request not found")
        
        data = request.data.copy()
        data['service_request'] = service_request.id
        data['service_provider'] = service_provider.id
        
        serializer = ServiceRequestBidSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class CancelBookingView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
        service_provider = get_user_from_token(request)
        try:
            booking = Booking.objects.get(id=booking_id, service_provider=service_provider)
        except Booking.DoesNotExist:
            raise NotFound("Booking not found")
        
        booking.provider_status = 'Cancelled'
        booking.save()
        return Response({"message": "Booking cancelled successfully"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class CompleteBookingView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id, *args, **kwargs):
        service_provider = get_user_from_token(request)
        try:
            booking = Booking.objects.get(id=booking_id, service_provider=service_provider)
        except Booking.DoesNotExist:
            raise NotFound("Booking not found")
        
        booking.provider_status = 'Completed'
        booking.save()
        return Response({"message": "Booking completed successfully"}, status=status.HTTP_200_OK)
