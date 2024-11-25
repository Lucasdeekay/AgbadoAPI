from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import ServiceProvider
from .serializers import ServiceProviderSerializer


class CustomPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page


class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['name', 'status', 'category']  # Fields you want to filter by
