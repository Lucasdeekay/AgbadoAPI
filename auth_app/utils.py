import random
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from .models import OTP


# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))


# Create OTP in the database
def create_otp(user):
    otp = generate_otp()
    otp_instance = OTP.objects.create(user=user, otp=otp)
    return otp_instance


# Send OTP via email
def send_otp_email(user, otp):
    subject = 'Your OTP for password reset'
    message = f'Your OTP to reset your password is: {otp}'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


# Send OTP via phone number (using Twilio as an example)
def send_otp_sms(user, otp):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f'Your OTP to reset your password is: {otp}',
        from_=settings.TWILIO_PHONE_NUMBER,
        to=user.phone_number
    )
    return message.sid


import requests
import json
import google.auth.transport.requests
from google.oauth2 import id_token
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


# Function to get Google user info
def get_google_user_info(token):
    try:
        id_info = id_token.verify_oauth2_token(token, google.auth.transport.requests.Request(),
                                               settings.GOOGLE_CLIENT_ID)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise AuthenticationFailed("Invalid Google token")
        return id_info
    except ValueError as e:
        raise AuthenticationFailed(f"Google token error: {str(e)}")


# Function to get Apple user info
def get_apple_user_info(client_id, authorization_code):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": settings.APPLE_CLIENT_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.APPLE_REDIRECT_URI
    }

    response = requests.post("https://appleid.apple.com/auth/token", data=data, headers=headers)
    if response.status_code != 200:
        raise AuthenticationFailed("Failed to fetch Apple user info")

    tokens = response.json()
    id_token_data = tokens.get("id_token")
    return id_token_data
