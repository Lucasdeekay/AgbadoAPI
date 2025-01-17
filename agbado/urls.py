"""
URL configuration for agbado project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from drf_yasg import openapi
# from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls

# Swagger documentation setup
# # schema_view = get_schema_view(
#     openapi.Info(
#         title="AgbaDo API",
#         default_version='v1',
#         description="AgbaDo API",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@agbadoapi.local"),
#         license=openapi.License(name="MIT License"),
#     ),
#     public=True,
#     permission_classes=[permissions.AllowAny],
# )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),  # Include the auth app URLs
    path('wallet/', include('wallet_app.urls')),  # Include the wallet app URLs
    path('provider/', include('provider_app.urls')),  # Include the provider app URLs
    path('service/', include('service_app.urls')),  # Include the service app URLs
    path('user/', include('user_app.urls')),  # Include the user app URLs
    path('notification/', include('notification_app.urls')),  # Include the notification app URLs
    # path('docs/', include_docs_urls(title='AgbaDo API Documentation', public=True)),
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
