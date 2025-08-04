"""
Authentication app views for handling user registration, login, and authentication.

This module contains views for user registration, login, OTP verification, PIN management,
WebAuthn biometric authentication, and account management operations.
"""

"""
Authentication app views for handling user registration, login, and authentication.

This module contains views for user registration, login, OTP verification, PIN management,
WebAuthn biometric authentication, and account management operations.
"""

from django.shortcuts import redirect
import jwt
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import base64
import os
import hashlib
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.db import IntegrityError, transaction
from django.db import DatabaseError
from django.utils import timezone


from django.conf import settings
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    PublicKeyCredentialDescriptor,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement
)

from agbado import settings
from notification_app.models import Notification
from user_app.models import UserReward
from .serializers import UserSerializer
from .models import User as CustomUser, OTP, Referral, WebAuthnCredential
from .utils import create_otp, send_otp_email, send_otp_sms, write_to_file
import logging


logger = logging.getLogger(__name__)

# Reward for referring a user (subject to change)
REFERRAL_REWARD = 50


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

    except Token.DoesNotExist:
        raise AuthenticationFailed('Invalid token')
    except (IndexError, ValueError):
        raise AuthenticationFailed('Invalid Authorization header format')


def delete_token(request):
    """
    Deletes the token from the Authorization header.

    :param request: The current request object
    :raises: AuthenticationFailed if token is invalid or missing
    """
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        token = Token.objects.get(key=token)
        token.delete()

    except Token.DoesNotExist:
        raise AuthenticationFailed('Invalid token')
    except (IndexError, ValueError):
        raise AuthenticationFailed('Invalid Authorization header format')

class RegisterServiceProviderView(APIView):
    """
    Register a new service provider user.
    
    Creates a new user account with service provider privileges.
    Handles referral codes and sends OTP for verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Register a new service provider user.
        
        Required fields: first_name, last_name, email, phone, password
        Optional fields: state, referral_code
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone')
        state = request.data.get('state')
        password = request.data.get('password')
        referral_code = request.data.get('referral_code')

        if not email or not phone_number or not password:
            return Response(
                {"message": "Email, phone number, and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"message": "A user with this email already exists."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "A user with this phone number already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
                user.is_service_provider = True

                # Handle referral if referral_code was provided
                if referral_code and CustomUser.objects.filter(referral_code=referral_code).exists():
                    referer = CustomUser.objects.get(referral_code=referral_code)
                    Referral.objects.create(user=user, referer=referer)

                user.save()

                # Generate and send OTP
                otp_instance = create_otp(user)
                otp = otp_instance.otp

                token, created = Token.objects.get_or_create(user=user)
                
                logger.info(f"Service provider registered successfully: {user.email}")
                
                return Response({
                    "token": token.key,
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(APIView):
    """
    Register a new regular user.
    
    Creates a new user account with standard privileges.
    Handles referral codes and sends OTP for verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Register a new regular user.
        
        Required fields: first_name, last_name, email, phone, password
        Optional fields: state, referral_code
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone')
        state = request.data.get('state')
        password = request.data.get('password')
        referral_code = request.data.get('referral_code')

        if not email or not phone_number or not password:
            return Response(
                {"message": "Email, phone number, and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"message": "A user with this email already exists."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if CustomUser.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {"message": "A user with this phone number already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

                # Handle referral if referral_code was provided
                if referral_code and CustomUser.objects.filter(referral_code=referral_code).exists():
                    referer = CustomUser.objects.get(referral_code=referral_code)
                    Referral.objects.create(user=user, referer=referer)
                    user_reward, created = UserReward.objects.get_or_create(user=referer)
                    user_reward.points += REFERRAL_REWARD
                    user_reward.save()

                user.save()

                # Generate and send OTP
                otp_instance = create_otp(user)
                otp = otp_instance.otp

                token, created = Token.objects.get_or_create(user=user)
                
                logger.info(f"User registered successfully: {user.email}")
                
                return Response({
                    "token": token.key,
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)


class SendOTPView(APIView):
    """
    Send OTP to user for verification.
    
    Sends OTP via email or SMS based on the provided identifier.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Send OTP to user for verification.
        
        Required fields: identifier (email or phone number)
        """
        identifier = request.data.get('identifier')

        if not identifier:
            return Response(
                {"message": "Identifier (email or phone) is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
                # Generate and send OTP
                otp_instance = create_otp(user)
                otp = otp_instance.otp
                # Send OTP to email
                send_otp_email(user, otp)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
                # Generate and send OTP
                otp_instance = create_otp(user)
                otp = otp_instance.otp
                # Send OTP to phone
                send_otp_sms(user, otp)

            logger.info(f"OTP sent successfully to {identifier}")
            return Response(
                {"message": "OTP successfully sent. You can now log in."}, 
                status=status.HTTP_200_OK
            )

        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)


        return Response({"message": "OTP successfully sent. You can now log in."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    Verify OTP and activate user account.
    
    Verifies the provided OTP and marks the user as verified.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Verify OTP and activate user account.
        
        Required fields: identifier (email or phone), otp
        """
        identifier = request.data.get('identifier')
        otp = request.data.get('otp')

        if not identifier or not otp:
            return Response(
                {"message": "Identifier (email or phone) and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)

            # Check OTP validity
            existing_otp = OTP.objects.filter(user=user, otp=otp, is_used=False).last()

            if not existing_otp:
                return Response(
                    {"message": "Invalid OTP."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if existing_otp.is_expired():
                return Response(
                    {"message": "OTP has expired."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Mark user as verified
            user.is_verified = True
            user.is_active = True
            user.save()

            # Mark OTP as used
            existing_otp.is_used = True
            existing_otp.save()

            logger.info(f"User account verified successfully: {user.email}")
            return Response(
                {"message": "Account verified successfully. You can now log in."}, 
                status=status.HTTP_200_OK
            )

        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User with the provided email or phone number does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return Response(
                {"message": f"An error occurred during verification: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PinRegistrationView(APIView):
    """
    Register a new PIN for the user.
    
    Allows users to set a 6-digit PIN for additional security.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Register a new PIN for the user.
        
        Required fields: pin (6-digit number)
        """
        user = get_user_from_token(request)
        pin = request.data.get("pin")
        
        if not pin or len(pin) != 6 or not pin.isdigit():
            return Response(
                {"message": "PIN must be a 6-digit number."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.pin:
            return Response(
                {"message": "PIN already exists. Use the update endpoint to change it."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.pin = pin
            user.save()
            
            logger.info(f"PIN registered successfully for user: {user.email}")
            return Response(
                {"message": "PIN registered successfully."}, 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error registering PIN for user {user.email}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PinUpdateView(APIView):
    """
    Update the user's PIN.
    
    Allows users to change their existing PIN.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        Update the user's PIN.
        
        Required fields: pin (6-digit number)
        """
        user = get_user_from_token(request)
        pin = request.data.get("pin")

        if not pin or len(pin) != 6 or not pin.isdigit():
            return Response(
                {"message": "PIN must be a 6-digit number."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.pin:
            return Response(
                {"message": "PIN does not exist. Use the registration endpoint to set it."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.pin = pin
            user.save()
            
            logger.info(f"PIN updated successfully for user: {user.email}")
            return Response(
                {"message": "PIN updated successfully."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating PIN for user {user.email}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PinAuthView(APIView):
    """
    Authenticate user using PIN.
    
    Verifies the user's PIN for additional security.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Authenticate user using PIN.
        
        Required fields: pin (6-digit number)
        """
        user = get_user_from_token(request)
        pin = request.data.get("pin")

        if not pin or len(pin) != 6 or not pin.isdigit():
            return Response(
                {"message": "PIN must be a 6-digit number."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.pin != pin:
            return Response(
                {"message": "Invalid PIN. Try again"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response({"message": "PIN authentication successfully."}, status=status.HTTP_200_OK)




class LoginView(APIView):
    """
    Login user using email/phone and password.
    
    Authenticates user and returns a token for API access.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Login user using email/phone and password.
        
        Required fields: identifier (email or phone), password
        """
        identifier = request.data.get('identifier')
        password = request.data.get('password')

        if not identifier or not password:
            return Response(
                {"message": "Identifier (email or phone) and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
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

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return Response(
                {"message": f"An error occurred during login: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if user is not None:
            login(request, user)
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
            return Response({"message": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

    

class LogoutView(APIView):
    """
    Logout user and delete their token.
    
    Removes the user's authentication token and logs them out.
    """
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        """
        Logout user and delete their token.
        """
        try:
            user = get_user_from_token(request)
            delete_token(request)
            logout(request)
            
            logger.info(f"User logged out successfully: {user.email}")
            return Response(
                {"message": "Logged out successfully."}, 
                status=status.HTTP_200_OK
            )
        except AuthenticationFailed as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    """
    Request OTP for password reset.
    
    Sends OTP to user's email or phone for password reset.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Request OTP for password reset.
        
        Required fields: identifier (email or phone number)
        """
        identifier = request.data.get('identifier')

        if not identifier:
            return Response(
                {"message": "Email or Phone number is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)

            # Check if there's an existing OTP and it's still valid
            existing_otp = OTP.objects.filter(user=user, is_used=False).last()
            if existing_otp and not existing_otp.is_expired():
                return Response(
                    {"message": "An OTP was already sent. Please check your email/phone."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate and save OTP
            otp_instance = create_otp(user)
            otp = otp_instance.otp

            # Send OTP to email and phone
            if '@' in identifier:
                send_otp_email(user, otp)
            else:
                send_otp_sms(user, otp)

        except Exception as e:
            logger.error(f"Error sending OTP to {identifier}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        return Response({"message": "OTP sent to your email and phone number."}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    Reset password using OTP.
    
    Allows users to reset their password without OTP verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Reset password using OTP.
        
        Required fields: identifier (email or phone), new_password
        """
        identifier = request.data.get('identifier')
        new_password = request.data.get('new_password')

        if not identifier or not new_password:
            return Response(
                {"message": "Identifier (email or phone) and new password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)

            # Update password
            user.set_password(new_password)
            user.save()

            Notification.objects.create(
                user=user, 
                title="Password Reset Successful", 
                message="Your password has been successfully reset."
            )
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )  

        return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)


class UpdateIsBusyView(APIView):
    """
    Update user's busy status.
    
    Toggles the is_busy field for the authenticated user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        Update user's busy status.
        """
        user = get_user_from_token(request)

        try:
            # Toggle the is_busy field
            user.is_busy = not user.is_busy
            user.save()

            logger.info(f"User busy status updated: {user.email} - {user.is_busy}")
            return Response({
                'is_busy': user.is_busy,
                'message': 'Successfully updated user status.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error updating user busy status: {str(e)}")
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAppleAuthView(APIView):
    """
    Handle Google/Apple authentication.
    
    Processes social authentication and either logs in existing users
    or redirects to registration for new users.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle Google/Apple authentication.
        
        Required fields: email, first_name, last_name
        Optional fields: phone_number, state, password, referral_code
        """
        data = request.data

        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_number")
        password = data.get("password")
        state = data.get('state')
        referral_code = data.get('referral_code')

        if not email:
            return Response(
                {"message": "Email is required for social authentication."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if user already exists
            user = CustomUser.objects.get(email=email)
            # If user exists, login and return data
            login(request, user)

            Notification.objects.create(
                user=user, 
                title="Login Successful", 
                message="You have successfully logged in via Google/Apple."
            )
            
            logger.info(f"Social login successful for user: {user.email}")
            return Response({
                "message": "Login successful",
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": getattr(user, 'phone_number', None)
                }
            }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            # If user doesn't exist, register them
            logger.info(f"New user attempting social registration: {email}")
            return redirect('register')


# --- WebAuthn (FIDO2) Biometric Authentication Views ---


class StartWebAuthnRegistrationView(APIView):
    """
    Start WebAuthn registration process.
    
    Generates registration options for biometric authentication setup.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Start WebAuthn registration process.
        """
        user = get_user_from_token(request)
        if not user:
            return Response(
                {"message": "Authentication failed: User not found."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate unique user_id for WebAuthn (can be user.id or a UUID)
        webauthn_user_id = str(user.id).encode('utf-8')

        # Get existing credential IDs for exclusion
        existing_credentials = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [
            PublicKeyCredentialDescriptor(
                id=base64.urlsafe_b64decode(cred.credential_id + '==='),
                type='public-key',
                transports=[t.strip() for t in cred.transports.split(',')] if cred.transports else None
            ) for cred in existing_credentials
        ]

        try:
            options = generate_registration_options(
                rp_id=settings.WEBAUTHN_RP_ID,
                rp_name=settings.WEBAUTHN_RP_NAME,
                user_id=webauthn_user_id,
                user_name=user.email,
                user_display_name=user.email,
                exclude_credentials=exclude_credentials,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    user_verification=UserVerificationRequirement.PREFERRED,
                ),
                attestation='direct'
            )
            # Store the challenge in session or a temporary DB record
            request.session['challenge'] = base64.urlsafe_b64encode(options.challenge).decode('utf-8').rstrip("=")
            request.session['user_id_for_webauthn_reg'] = str(user.id)

            logger.info(f"WebAuthn registration started for user: {user.email}")
            return Response({
                "publicKeyCredentialCreationOptions": options.json
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error starting WebAuthn registration for user {user.email}: {e}")
            return Response({"message": f"Failed to start WebAuthn registration: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompleteWebAuthnRegistrationView(APIView):
    """
    Complete WebAuthn registration process.
    
    Verifies the registration response and saves the credential.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Complete WebAuthn registration process.
        """
        user = get_user_from_token(request)
        if not user:
            return Response(
                {"message": "Authentication failed: User not found."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Retrieve the challenge and user ID from session/temporary storage
        stored_challenge = request.session.pop('challenge', None)
        stored_user_id_for_webauthn_reg = request.session.pop('user_id_for_webauthn_reg', None)

        if not stored_challenge or stored_user_id_for_webauthn_reg != str(user.id):
            return Response(
                {"message": "Invalid or expired registration challenge."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Decode the base64url challenge
            decoded_challenge = base64.urlsafe_b64decode(stored_challenge + '===')

            # Parse the client's response
            registration_response = RegistrationCredential.parse_raw(request.body)

            # Verify the registration response
            verification = verify_registration_response(
                credential=registration_response,
                expected_challenge=decoded_challenge,
                expected_origin=request.headers.get('Origin') or f"{request.scheme}://{request.get_host()}",
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                require_user_verification=False
            )

            # Save the new credential
            credential_id_b64 = base64.urlsafe_b64encode(verification.credential_id).decode('utf-8').rstrip("=")
            public_key_b64 = base64.urlsafe_b64encode(verification.credential_public_key).decode('utf-8').rstrip("=")

            with transaction.atomic():
                WebAuthnCredential.objects.create(
                    user=user,
                    credential_id=credential_id_b64,
                    public_key=public_key_b64,
                    sign_count=verification.sign_count,
                    transports=','.join(registration_response.response.transports) if registration_response.response.transports else None
                )

            logger.info(f"WebAuthn credential registered successfully for user: {user.email}")
            return Response(
                {"message": "WebAuthn credential registered successfully.", "credential_id": credential_id_b64}, 
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            logger.warning(f"WebAuthn registration verification failed for user {user.email}: {e}")
            return Response(
                {"message": f"WebAuthn verification failed: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except DatabaseError:
            return Response(
                {"message": "A database error occurred while saving the credential."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error completing WebAuthn registration for user {user.email}: {e}")
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class StartWebAuthnAuthenticationView(APIView):
    """
    Start WebAuthn authentication process.
    
    Generates authentication options for biometric login.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Start WebAuthn authentication process.
        
        Required fields: email
        """
        email = request.data.get('email')
        if not email:
            return Response(
                {"message": "Email is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all registered credentials for this user
        user_credentials = WebAuthnCredential.objects.filter(user=user)
        if not user_credentials.exists():
            return Response(
                {"message": "No WebAuthn credentials registered for this user. Please use password login or register biometrics first."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        allow_credentials = [
            PublicKeyCredentialDescriptor(
                id=base64.urlsafe_b64decode(cred.credential_id + '==='),
                type='public-key',
                transports=[t.strip() for t in cred.transports.split(',')] if cred.transports else None
            ) for cred in user_credentials
        ]

        try:
            options = generate_authentication_options(
                rp_id=settings.WEBAUTHN_RP_ID,
                allow_credentials=allow_credentials,
                user_verification=UserVerificationRequirement.PREFERRED
            )
            # Store the challenge in session or a temporary DB record
            request.session['challenge'] = base64.urlsafe_b64encode(options.challenge).decode('utf-8').rstrip("=")
            request.session['user_id_for_webauthn_auth'] = str(user.id)

            logger.info(f"WebAuthn authentication started for user: {user.email}")
            return Response({
                "publicKeyCredentialRequestOptions": options.json
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error starting WebAuthn authentication for user {user.email}: {e}")
            return Response(
                {"message": f"Failed to start WebAuthn authentication: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CompleteWebAuthnAuthenticationView(APIView):
    """
    Complete WebAuthn authentication process.
    
    Verifies the authentication response and logs the user in.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Complete WebAuthn authentication process.
        """
        # Retrieve the challenge and user ID from session/temporary storage
        stored_challenge = request.session.pop('challenge', None)
        stored_user_id_for_webauthn_auth = request.session.pop('user_id_for_webauthn_auth', None)

        if not stored_challenge or not stored_user_id_for_webauthn_auth:
            return Response(
                {"message": "Invalid or expired authentication challenge."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(id=int(stored_user_id_for_webauthn_auth))
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User not found for authentication."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Decode the base64url challenge
            decoded_challenge = base64.urlsafe_b64decode(stored_challenge + '===')

            # Parse the client's response
            auth_response = AuthenticationCredential.parse_raw(request.body)

            # Retrieve the credential from your DB using the credential ID sent by client
            credential_id_b64 = base64.urlsafe_b64encode(auth_response.id).decode('utf-8').rstrip("=")
            stored_credential = WebAuthnCredential.objects.get(
                user=user,
                credential_id=credential_id_b64
            )

            verification = verify_authentication_response(
                credential=auth_response,
                expected_challenge=decoded_challenge,
                expected_origin=request.headers.get('Origin') or f"{request.scheme}://{request.get_host()}",
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                credential_public_key=base64.urlsafe_b64decode(stored_credential.public_key + '==='),
                credential_sign_count=stored_credential.sign_count,
                require_user_verification=False
            )

            # Update sign count to prevent replay attacks
            stored_credential.sign_count = verification.new_sign_count
            stored_credential.last_used = timezone.now()
            stored_credential.save()

            # Successful authentication, generate/retrieve user token
            token, created = Token.objects.get_or_create(user=user)

            logger.info(f"WebAuthn authentication successful for user: {user.email}")
            return Response({
                "message": "WebAuthn login successful.",
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except WebAuthnCredential.DoesNotExist:
            return Response(
                {"message": "WebAuthn credential not found for this user."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            logger.warning(f"WebAuthn authentication verification failed for user {user.email}: {e}")
            return Response(
                {"message": f"WebAuthn authentication failed: {str(e)}"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except DatabaseError:
            return Response(
                {"message": "A database error occurred during authentication."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error completing WebAuthn authentication for user {user.email}: {e}")
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteWebAuthnCredentialView(APIView):
    """
    Delete WebAuthn credential.
    
    Allows users to remove their biometric authentication credentials.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """
        Delete WebAuthn credential.
        
        URL parameter: pk (credential ID)
        """
        user = get_user_from_token(request)
        if not user:
            return Response(
                {"message": "Authentication failed: User not found."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            credential = WebAuthnCredential.objects.get(pk=pk, user=user)
            credential.delete()
            
            logger.info(f"WebAuthn credential deleted for user: {user.email}")
            return Response(
                {"message": "WebAuthn credential deleted successfully."}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except WebAuthnCredential.DoesNotExist:
            return Response(
                {"message": "Credential not found or does not belong to this user."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError:
            return Response(
                {"message": "A database error occurred while deleting the credential."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListWebAuthnCredentialsView(APIView):
    """
    List user's WebAuthn credentials.
    
    Returns all biometric authentication credentials for the user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List user's WebAuthn credentials.
        """
        user = get_user_from_token(request)
        if not user:
            return Response(
                {"message": "Authentication failed: User not found."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        credentials = WebAuthnCredential.objects.filter(user=user).order_by('-registered_at')
        data = [
            {
                "id": cred.id,
                "credential_id_short": cred.credential_id[:10] + "...", # Shorten for display
                "registered_at": cred.registered_at.isoformat(),
                "last_used": cred.last_used.isoformat() if cred.last_used else None,
                "transports": cred.transports,
                "sign_count": cred.sign_count
            } for cred in credentials
        ]
        return Response({"credentials": data}, status=status.HTTP_200_OK)

# New view for deleting a user account

class DeleteAccountView(APIView):
    """
    Delete user account.
    
    Permanently deletes the authenticated user's account and all associated data.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """
        Delete user account.
        """
        user = get_user_from_token(request)

        try:
            user_email = user.email
            user.delete()

            logger.info(f"User account {user_email} deleted successfully.")

            # After deleting the user, ensure their token is also gone
            logout(request)

            return Response(
                {"message": "Account deleted successfully."}, 
                status=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            logger.error(f"Error deleting account for user {user.email if user else 'unknown'}: {e}")
            return Response({
                "message": f"An unexpected error occurred while deleting the account: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)