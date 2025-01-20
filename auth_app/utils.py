import random
from django.core.mail import send_mail
from twilio.rest import Client

from agbado import settings
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
        to="+2349024563447"
    )
    return message.sid


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