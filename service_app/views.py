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
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class ServiceDetailsView(APIView):
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
