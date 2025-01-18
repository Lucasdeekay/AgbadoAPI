from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.views import get_user_from_token
from provider_app.models import ServiceProvider
from provider_app.serializers import ServiceProviderSerializer
from service_app.models import SubService, Service, Booking
from service_app.serializers import ServiceSerializer, SubServiceSerializer

@method_decorator(csrf_exempt, name='dispatch')
class ServiceProviderDetailsView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = get_user_from_token(request)

            # Fetch service provider details
            service_provider = get_object_or_404(ServiceProvider, user=user)
            provider_data = ServiceProviderSerializer(service_provider).data

            # Fetch services provided by the service provider
            services = Service.objects.filter(provider=service_provider)
            services_data = ServiceSerializer(services, many=True).data

            # Fetch reviews from the Booking model
            bookings = Booking.objects.filter(service_provider=service_provider).exclude(feedback=None)
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

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    # permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ServiceSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Service added successfully.", "service": serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class AddSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubServiceSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Subservice added successfully.", "subservice": serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def put(self, request, service_id):
        service = get_object_or_404(Service, id=service_id)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Service updated successfully.", "service": serializer.data},
                            status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class EditSubServiceView(APIView):
    authentication_classes = [TokenAuthentication]

    # permission_classes = [IsAuthenticated]

    def put(self, request, subservice_id):
        subservice = get_object_or_404(SubService, id=subservice_id)
        serializer = SubServiceSerializer(subservice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Subservice updated successfully.", "subservice": serializer.data},
                            status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
