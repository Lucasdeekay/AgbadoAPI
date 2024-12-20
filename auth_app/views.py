import jwt
from rest_framework import status, permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from agbado import settings
from .serializers import UserSerializer
from .models import User as CustomUser, OTP, Referral
from .utils import create_otp, send_otp_email, send_otp_sms, get_google_user_info, get_apple_user_info


def get_user_from_token(request):
    """
    Extracts the user from the token in the Authorization header.

    :param request: The current request object
    :return: The user associated with the token
    :raises: AuthenticationFailed if token is invalid or missing
    """
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        token = Token.objects.get(key=token)
        return token.user
    except Exception:
        raise AuthenticationFailed('Invalid token')


class RegisterView(APIView):
    def post(self, request):
        """
        Register a new user. Either email or phone number is required.
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        state = request.data.get('state')
        password = request.data.get('password')
        referral_code = request.data.get('referral_code')

        if not email or not phone_number or not password:
            return Response({"error": "Email, phone number, and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response({"error": "A user with this phone number already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not CustomUser.objects.filter(referral_code=referral_code).exists():
            return Response({"error": "The referral code matches no existing user."},
                            status=status.HTTP_400_BAD_REQUEST)

        referer = CustomUser.objects.get(referral_code=referral_code)

        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone_number': phone_number,
            'state': state,
            'password': password
        }
        serializer = UserSerializer(data=user_data)

        if serializer.is_valid():
            user = serializer.save()
            user.set_password(password)
            user.save()

            user.is_active = False  # Deactivate account until verification
            user.save()

            Referral.objects.create(user=user, referer=referer)

            # Generate and send OTP
            otp_instance = create_otp(user)
            otp = otp_instance.otp

            # Send OTP to email and phone
            send_otp_email(user, otp)
            send_otp_sms(user, otp)

            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    def post(self, request):
        """
        Verify the user's registration using OTP.
        """
        identifier = request.data.get('identifier')  # email or phone number
        otp = request.data.get('otp')

        if not identifier or not otp:
            return Response({"error": "Identifier (email or phone) and OTP are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check OTP validity
        existing_otp = OTP.objects.filter(user=user, otp=otp, is_used=False).last()

        if not existing_otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if existing_otp.is_expired():
            return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark user as verified
        user.is_verified = True
        user.is_active = True  # Activate account after verification
        user.save()

        # Mark OTP as used
        existing_otp.is_used = True
        existing_otp.save()

        return Response({"message": "Account verified successfully. You can now log in."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    def post(self, request):
        """
        Login the user using email or phone number and password.
        """
        identifier = request.data.get('identifier')  # This can be email or phone number
        password = request.data.get('password')

        if not identifier or not password:
            return Response({"error": "Identifier (email or phone) and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Attempt authentication using email
        user = None
        if '@' in identifier:
            # If identifier contains '@', treat it as email
            user = authenticate(request, email=identifier, password=password)
        else:
            # Else, treat it as phone number
            try:
                user = CustomUser.objects.get(phone_number=identifier)
                if not user.check_password(password):
                    user = None
            except CustomUser.DoesNotExist:
                user = None

        if user is not None:
            # Create and return token if credentials are valid
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": {
                    "email": user.email,
                    "phone_number": user.phone_number,
                }
            })
        else:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Logout the user and delete their token.
        """
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    def post(self, request):
        """
        Request OTP for password reset.
        User can provide either email or phone number.
        OTP will be sent to the provided identifier.
        """
        identifier = request.data.get('identifier')  # email or phone number

        if not identifier:
            return Response({"error": "Email or Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if there's an existing OTP and it’s still valid
        existing_otp = OTP.objects.filter(user=user, is_used=False).last()
        if existing_otp and not existing_otp.is_expired():
            return Response({"error": "An OTP was already sent. Please check your email/phone."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Generate and save OTP
        otp_instance = create_otp(user)
        otp = otp_instance.otp

        # Send OTP to email and phone
        if '@' in identifier:
            send_otp_email(user, otp)
        else:
            send_otp_sms(user, otp)


        return Response({"message": "OTP sent to your email and phone number."}, status=status.HTTP_200_OK)


class RetrievePasswordView(APIView):
    def post(self, request):
        """
        Retrieve and reset password using OTP.
        User provides OTP and a new password.
        """
        identifier = request.data.get('identifier')  # email or phone number
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        if not identifier or not otp or not new_password:
            return Response({"error": "Identifier (email or phone), OTP, and new password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check OTP validity
        existing_otp = OTP.objects.filter(user=user, otp=otp, is_used=False).last()

        if not existing_otp:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if existing_otp.is_expired():
            return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        existing_otp.is_used = True
        existing_otp.save()

        return Response({"message": "OTP successfully verified."}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    def post(self, request):
        """
        Retrieve and reset password using OTP.
        User provides OTP and a new password.
        """
        identifier = request.data.get('identifier')  # email or phone number
        new_password = request.data.get('new_password')

        if not identifier or not new_password:
            return Response({"error": "Identifier (email or phone), OTP, and new password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)
        # Update password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)



class GoogleAuthView(APIView):
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_info = get_google_user_info(token)
            email = user_info["email"]
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            user, _ = CustomUser.objects.get_or_create(email=email)
            user.first_name = first_name
            user.last_name = last_name
            user.is_verified = True
            user.save()

            auth_token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": auth_token.key}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AppleAuthView(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Authorization code is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            id_token = get_apple_user_info(settings.APPLE_CLIENT_ID, code)
            decoded_token = jwt.decode(id_token, options={"verify_signature": False})
            email = decoded_token.get("email", None)

            if not email:
                return Response({"error": "Apple ID token did not contain email"}, status=status.HTTP_400_BAD_REQUEST)

            user, _ = CustomUser.objects.get_or_create(email=email)
            user.is_verified = True
            user.save()

            auth_token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": auth_token.key}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
