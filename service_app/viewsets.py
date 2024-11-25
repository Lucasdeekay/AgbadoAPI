from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Service, SubService, ServiceRequest
from .serializers import ServiceSerializer, SubServiceSerializer, ServiceRequestSerializer


class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['name', 'category', 'status']  # Fields you want to filter by


class SubServiceViewSet(viewsets.ModelViewSet):
    queryset = SubService.objects.all()
    serializer_class = SubServiceSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['service', 'name', 'price']  # Fields you want to filter by


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['service', 'user', 'status']  # Fields you want to filter by
