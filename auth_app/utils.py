import random
import re
from django.core.mail import send_mail
import requests

from agbado import settings
from .models import OTP


# Generate OTP
def generate_otp():
    return str(random.randint(10000, 99999))


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


def format_phone_number(phone_number: str) -> str:
    """Format phone number to E.164 standard (e.g., 2349024563447)"""
    phone_number = phone_number.strip()  # Remove spaces
    phone_number = re.sub(r"\D", "", phone_number)  # Remove non-digit characters

    # Remove leading 0 if it starts with 0
    if phone_number.startswith("0"):
        phone_number = phone_number[1:]

    # Ensure it starts with 234 (Nigeria)
    # The original logic for '+234' was a bit off for the desired output.
    # Let's adjust it.
    if phone_number.startswith("234"):
        # Already starts with 234, no need to do anything
        pass
    elif phone_number.startswith("+234"): # This part was slightly incorrect in original.
        phone_number = phone_number[1:] # Remove the leading '+'
    else:
        # If it's a Nigerian number without 234 or +234, prepend 234
        # This assumes numbers without 234 prefix are Nigerian.
        # You might need more robust country-code detection for international apps.
        phone_number = "234" + phone_number

    return phone_number # Removed f-string as it's not strictly necessary here

def send_otp_sms(user, otp):
    """
    Sends an SMS message using the Termii API.

    Args:
        to_number (str): The recipient's phone number in international format (e.g., "2348012345678").
        message (str): The content of the SMS message.
        sender_id (str, optional): The sender ID for the message. Defaults to "Termii".
                                   You can register custom sender IDs on Termii.

    Returns:
        dict or None: A dictionary containing the API response on success, None on failure.
    """
    api_key = settings.TERMII_LIVE_KEY
    api_url = "https://v3.api.termii.com/api/sms/send"

    if not api_key:
        print("Termii API key not configured in settings.")
        return None

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "to": user.phone_number,
        "from": 'Agba-do!',
        "sms": f'Your OTP to reset your password is: {otp}',
        "type": "plain",
        "channel": "generic",
        "api_key": api_key
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending SMS via Termii: {e}")
        return None


def write_to_file(file_path, message, error=None):
    """
    Writes a message and an optional error to a file.
    
    :param file_path: Path to the file where logs will be written.
    :param message: The main message to write.
    :param error: (Optional) Error message to log.
    """
    try:
        with open(file_path, "a") as file:
            file.write(f"Message: {message}\n")
            if error:
                file.write(f"Error: {error}\n")
            file.write("-" * 50 + "\n")  # Separator for readability
    except Exception as e:
        print(f"Failed to write to file: {e}")