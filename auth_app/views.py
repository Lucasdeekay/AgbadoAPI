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
from .serializers import UserSerializer
from .models import User as CustomUser, OTP, Referral
from .utils import create_otp, send_otp_email, send_otp_sms, write_to_file


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

@method_decorator(csrf_exempt, name='dispatch')
class RegisterServiceProviderView(APIView):
    def post(self, request):
        """
        Register a new user. Either email or phone number is required.
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone')
        state = request.data.get('state')
        password = request.data.get('password')
        referral_code = request.data.get('referral_code')

        if not email or not phone_number or not password:
            return Response({"message": "Email, phone number, and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            return Response({"message": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response({"message": "A user with this phone number already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(referral_code=referral_code).exists():
            referer = CustomUser.objects.get(referral_code=referral_code)
            Referral.objects.create(user=user, referer=referer)

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

            # user.is_active = False  # Deactivate account until verification
            user.save()

            # Generate and send OTP
            otp_instance = create_otp(user)
            otp = otp_instance.otp

            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterUserView(APIView):
    def post(self, request):
        """
        Register a new user. Either email or phone number is required.
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone')
        state = request.data.get('state')
        password = request.data.get('password')
        referral_code = request.data.get('referral_code')

        if not email or not phone_number or not password:
            return Response({"message": "Email, phone number, and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            return Response({"message": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return Response({"message": "A user with this phone number already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(referral_code=referral_code).exists():
            referer = CustomUser.objects.get(referral_code=referral_code)
            Referral.objects.create(user=user, referer=referer)

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

            # user.is_active = False  # Deactivate account until verification
            user.save()

            # Generate and send OTP
            otp_instance = create_otp(user)
            otp = otp_instance.otp

            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SendOTPView(APIView):
    def post(self, request):
        """
        Verify the user's registration using OTP.
        """
        identifier = request.data.get('identifier')  # email or phone number

        if not identifier:
            return Response({"message": "Identifier (email or phone) and OTP are required."},
                            status=status.HTTP_400_BAD_REQUEST)

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
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)


        return Response({"message": "OTP successfully sent. You can now log in."}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPView(APIView):
    def post(self, request):
        """
        Verify the user's registration using OTP.
        """
        identifier = request.data.get('identifier')  # email or phone number
        otp = request.data.get('otp')

        if not identifier or not otp:
            return Response({"message": "Identifier (email or phone) and OTP are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check OTP validity
        existing_otp = OTP.objects.filter(user=user, otp=otp, is_used=False).last()

        if not existing_otp:
            return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if existing_otp.is_expired():
            return Response({"message": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark user as verified
        user.is_verified = True
        user.is_active = True  # Activate account after verification
        user.save()

        # Mark OTP as used
        existing_otp.is_used = True
        existing_otp.save()

        return Response({"message": "Account verified successfully. You can now log in."}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        """
        Login the user using email or phone number and password.
        """
        identifier = request.data.get('identifier')  # This can be email or phone number
        password = request.data.get('password')

        if not identifier or not password:
            return Response({"message": "Identifier (email or phone) and password are required."},
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

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        """
        Logout the user and delete their token.
        """
        try:
            user = get_user_from_token(request)  # Get the user (no deletion here)
            delete_token(request)             # Explicitly delete the token
            logout(request)  # Django's logout
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except AuthenticationFailed as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(APIView):
    def post(self, request):
        """
        Request OTP for password reset.
        User can provide either email or phone number.
        OTP will be sent to the provided identifier.
        """
        identifier = request.data.get('identifier')  # email or phone number

        if not identifier:
            return Response({"message": "Email or Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if there's an existing OTP and it’s still valid
        existing_otp = OTP.objects.filter(user=user, is_used=False).last()
        if existing_otp and not existing_otp.is_expired():
            return Response({"message": "An OTP was already sent. Please check your email/phone."},
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

@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(APIView):
    def post(self, request):
        """
        Retrieve and reset password using OTP.
        User provides OTP and a new password.
        """
        identifier = request.data.get('identifier')  # email or phone number
        new_password = request.data.get('new_password')

        if not identifier or not new_password:
            return Response({"message": "Identifier (email or phone), OTP, and new password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if identifier is email or phone number
            if '@' in identifier:
                user = CustomUser.objects.get(email=identifier)
            else:
                user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            return Response({"message": "User with the provided email or phone number does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Update password
        user.set_password(new_password)
        user.save()

        Notification.objects.create(user=user, title="Password Reset Successful", message="Your password has been successfully reset.")

        return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class UpdateIsBusyView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        Updates the is_busy field for the specified user.
        """
        user = get_user_from_token(request) # Replace with your actual user retrieval method.

        try:

            # Toggle the is_busy field
            user.is_busy = not user.is_busy
            user.save()

            return Response({
                'is_busy': user.is_busy,
                'message': 'Successfully updated user status.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleAppleAuthView(APIView):
    def post(self, request):
        data = request.data

        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        phone_number = data.get("phone_number")
        password = data.get("password")  # Not necessary for Google but can be used for registration
        state = data.get('state')
        password = data.get('password')
        referral_code = data.get('referral_code')

        # Check if user already exists
        try:
            user = CustomUser.objects.get(email=email)
            # If user exists, login and return data
            login(request, user)

            Notification.objects.create(user=user, title="Login Successful", message="You have successfully logged in via Google/Apple.")
            
            return Response({
                "message": "Login successful",
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": getattr(user.profile, 'phone_number', None)
                }
            }, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            # If user doesn't exist, register them
            return redirect('register')  # Redirect to the Register view (you can handle this in frontend)


# --- WebAuthn (FIDO2) Biometric Authentication Views ---

@method_decorator(csrf_exempt, name='dispatch')
class StartWebAuthnRegistrationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_token(request)
        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate unique user_id for WebAuthn (can be user.id or a UUID)
        webauthn_user_id = str(user.id).encode('utf-8')

        # Get existing credential IDs for exclusion
        existing_credentials = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [
            PublicKeyCredentialDescriptor(
                id=base64.urlsafe_b64decode(cred.credential_id + '==='), # pad if necessary
                type='public-key',
                transports=[t.strip() for t in cred.transports.split(',')] if cred.transports else None
            ) for cred in existing_credentials
        ]

        try:
            options = generate_registration_options(
                rp_id=settings.WEBAUTHN_RP_ID,
                rp_name=settings.WEBAUTHN_RP_NAME,
                user_id=webauthn_user_id,
                user_name=user.email, # Can be email or a unique username
                user_display_name=user.email,
                exclude_credentials=exclude_credentials,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    user_verification=UserVerificationRequirement.PREFERRED, # OR REQUIRED if you want biometrics mandatory
                    # resident_key=True # For passkeys - if you want discoverable credentials
                ),
                attestation='direct' # or 'none' for privacy, 'indirect' for security
            )
            # Store the challenge in session or a temporary DB record
            # IMPORTANT: For API-driven flow, associate challenge with a temporary ID and return that ID.
            # Don't use session directly with stateless APIs if not using session auth.
            request.session['challenge'] = base64.urlsafe_b64encode(options.challenge).decode('utf-8').rstrip("=")
            request.session['user_id_for_webauthn_reg'] = str(user.id) # Store user ID to link back

            return Response({
                "publicKeyCredentialCreationOptions": options.json
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error starting WebAuthn registration for user {user.email}: {e}")
            return Response({"message": f"Failed to start WebAuthn registration: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class CompleteWebAuthnRegistrationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = get_user_from_token(request)
        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        # Retrieve the challenge and user ID from session/temporary storage
        stored_challenge = request.session.pop('challenge', None)
        stored_user_id_for_webauthn_reg = request.session.pop('user_id_for_webauthn_reg', None)

        if not stored_challenge or stored_user_id_for_webauthn_reg != str(user.id):
            return Response({"message": "Invalid or expired registration challenge."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the base64url challenge
            decoded_challenge = base64.urlsafe_b64decode(stored_challenge + '===')

            # Parse the client's response
            registration_response = RegistrationCredential.parse_raw(request.body)

            # Verify the registration response
            verification = verify_registration_response(
                credential=registration_response,
                expected_challenge=decoded_challenge,
                expected_origin=request.headers.get('Origin') or f"{request.scheme}://{request.get_host()}", # Ensure this matches your frontend origin
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                require_user_verification=False # Set to True if user_verification in options was REQUIRED
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
                # Optionally set user.is_biometric_enabled = True if this is their first credential
                if not user.webauthn_credentials.exists():
                     # Consider adding this if you only allow one device or need a flag
                     # user.is_biometric_enabled = True
                     # user.save()
                    pass


            return Response({"message": "WebAuthn credential registered successfully.", "credential_id": credential_id_b64}, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.warning(f"WebAuthn registration verification failed for user {user.email}: {e}")
            return Response({"message": f"WebAuthn verification failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError:
            return Response({"message": "A database error occurred while saving the credential."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error completing WebAuthn registration for user {user.email}: {e}")
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class StartWebAuthnAuthenticationView(APIView):
    authentication_classes = [] # No token auth for initial login
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all registered credentials for this user
        user_credentials = WebAuthnCredential.objects.filter(user=user)
        if not user_credentials.exists():
            return Response({"message": "No WebAuthn credentials registered for this user. Please use password login or register biometrics first."}, status=status.HTTP_400_BAD_REQUEST)

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
                user_verification=UserVerificationRequirement.PREFERRED # OR REQUIRED
            )
            # Store the challenge in session or a temporary DB record
            request.session['challenge'] = base64.urlsafe_b64encode(options.challenge).decode('utf-8').rstrip("=")
            request.session['user_id_for_webauthn_auth'] = str(user.id)

            return Response({
                "publicKeyCredentialRequestOptions": options.json
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error starting WebAuthn authentication for user {user.email}: {e}")
            return Response({"message": f"Failed to start WebAuthn authentication: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class CompleteWebAuthnAuthenticationView(APIView):
    authentication_classes = [] # No token auth for initial login
    permission_classes = [AllowAny]

    def post(self, request):
        # Retrieve the challenge and user ID from session/temporary storage
        stored_challenge = request.session.pop('challenge', None)
        stored_user_id_for_webauthn_auth = request.session.pop('user_id_for_webauthn_auth', None)

        if not stored_challenge or not stored_user_id_for_webauthn_auth:
            return Response({"message": "Invalid or expired authentication challenge."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=int(stored_user_id_for_webauthn_auth))
        except User.DoesNotExist:
            return Response({"message": "User not found for authentication."}, status=status.HTTP_404_NOT_FOUND)

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
                expected_origin=request.headers.get('Origin') or f"{request.scheme}://{request.get_host()}", # Ensure this matches your frontend origin
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                credential_public_key=base64.urlsafe_b64decode(stored_credential.public_key + '==='),
                credential_sign_count=stored_credential.sign_count,
                require_user_verification=False # Set to True if user_verification in options was REQUIRED
            )

            # Update sign count to prevent replay attacks
            stored_credential.sign_count = verification.new_sign_count
            stored_credential.last_used = timezone.now()
            stored_credential.save()

            # Successful authentication, generate/retrieve user token
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "message": "WebAuthn login successful.",
                "token": token.key,
                "user": UserSerializer(user).data # Use your existing UserSerializer
            }, status=status.HTTP_200_OK)

        except WebAuthnCredential.DoesNotExist:
            return Response({"message": "WebAuthn credential not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            logger.warning(f"WebAuthn authentication verification failed for user {user.email}: {e}")
            return Response({"message": f"WebAuthn authentication failed: {str(e)}"}, status=status.HTTP_401_UNAUTHORIZED)
        except DatabaseError:
            return Response({"message": "A database error occurred during authentication."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error completing WebAuthn authentication for user {user.email}: {e}")
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteWebAuthnCredentialView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        user = get_user_from_token(request)
        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            credential = WebAuthnCredential.objects.get(pk=pk, user=user)
            credential.delete()
            return Response({"message": "WebAuthn credential deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except WebAuthnCredential.DoesNotExist:
            return Response({"message": "Credential not found or does not belong to this user."}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"message": "A database error occurred while deleting the credential."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class ListWebAuthnCredentialsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_user_from_token(request)
        if not user:
            return Response({"message": "Authentication failed: User not found."}, status=status.HTTP_401_UNAUTHORIZED)

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
