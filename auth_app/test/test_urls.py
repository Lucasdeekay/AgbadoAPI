from django.urls import reverse, resolve
from rest_framework.test import APITestCase

from auth_app.views import (
    RegisterServiceProviderView, RegisterUserView, SendOTPView, VerifyOTPView,
    LoginView, LogoutView, ForgotPasswordView, DeleteAccountView, ResetPasswordView,
    UpdateIsBusyView, PinRegistrationView, PinUpdateView, PinAuthView,
    GoogleAppleAuthView, StartWebAuthnRegistrationView, CompleteWebAuthnRegistrationView,
    StartWebAuthnAuthenticationView, CompleteWebAuthnAuthenticationView,
    ListWebAuthnCredentialsView, DeleteWebAuthnCredentialView
)
from auth_app.viewsets import UserViewSet, KYCViewSet, OTPViewSet, ReferralViewSet

class URLTests(APITestCase):
    """
    Test suite to verify that all URL patterns in the authentication app
    are correctly configured and resolve to the expected views.
    """

    def test_register_service_provider_url_resolves(self):
        """Test that the 'register-service-provider' URL resolves to the correct view."""
        url = reverse('register-service-provider')
        self.assertEqual(url, '/auth/register/service-provider/')
        self.assertEqual(resolve(url).func.view_class, RegisterServiceProviderView)

    def test_register_user_url_resolves(self):
        """Test that the 'register-user' URL resolves to the correct view."""
        url = reverse('register-user')
        self.assertEqual(url, '/auth/register/user/')
        self.assertEqual(resolve(url).func.view_class, RegisterUserView)

    def test_send_otp_url_resolves(self):
        """Test that the 'send-otp' URL resolves to the correct view."""
        url = reverse('send-otp')
        self.assertEqual(url, '/auth/send-otp/')
        self.assertEqual(resolve(url).func.view_class, SendOTPView)

    def test_verify_otp_url_resolves(self):
        """Test that the 'verify-otp' URL resolves to the correct view."""
        url = reverse('verify-otp')
        self.assertEqual(url, '/auth/verify-otp/')
        self.assertEqual(resolve(url).func.view_class, VerifyOTPView)

    def test_login_url_resolves(self):
        """Test that the 'login' URL resolves to the correct view."""
        url = reverse('login')
        self.assertEqual(url, '/auth/login/')
        self.assertEqual(resolve(url).func.view_class, LoginView)

    def test_logout_url_resolves(self):
        """Test that the 'logout' URL resolves to the correct view."""
        url = reverse('logout')
        self.assertEqual(url, '/auth/logout/')
        self.assertEqual(resolve(url).func.view_class, LogoutView)

    def test_forgot_password_url_resolves(self):
        """Test that the 'forgot-password' URL resolves to the correct view."""
        url = reverse('forgot-password')
        self.assertEqual(url, '/auth/forgot-password/')
        self.assertEqual(resolve(url).func.view_class, ForgotPasswordView)

    def test_delete_account_url_resolves(self):
        """Test that the 'delete-account' URL resolves to the correct view."""
        url = reverse('delete-account')
        self.assertEqual(url, '/auth/delete-account/')
        self.assertEqual(resolve(url).func.view_class, DeleteAccountView)

    def test_reset_password_url_resolves(self):
        """Test that the 'reset-password' URL resolves to the correct view."""
        url = reverse('reset-password')
        self.assertEqual(url, '/auth/reset-password/')
        self.assertEqual(resolve(url).func.view_class, ResetPasswordView)

    def test_update_status_url_resolves(self):
        """Test that the 'update-status' URL resolves to the correct view."""
        url = reverse('update-status')
        self.assertEqual(url, '/auth/update-status/')
        self.assertEqual(resolve(url).func.view_class, UpdateIsBusyView)

    # --- PIN Authentication URLs ---
    def test_pin_register_url_resolves(self):
        """Test that the 'pin-register' URL resolves to the correct view."""
        url = reverse('pin-register')
        self.assertEqual(url, '/auth/pin/register/')
        self.assertEqual(resolve(url).func.view_class, PinRegistrationView)

    def test_pin_update_url_resolves(self):
        """Test that the 'pin-update' URL resolves to the correct view."""
        url = reverse('pin-update')
        self.assertEqual(url, '/auth/pin/update/')
        self.assertEqual(resolve(url).func.view_class, PinUpdateView)

    def test_pin_auth_url_resolves(self):
        """Test that the 'pin-auth' URL resolves to the correct view."""
        url = reverse('pin-auth')
        self.assertEqual(url, '/auth/pin/auth/')
        self.assertEqual(resolve(url).func.view_class, PinAuthView)

    # --- Social Authentication URLs ---
    def test_google_apple_auth_url_resolves(self):
        """Test that the 'google-or-apple-auth' URL resolves to the correct view."""
        url = reverse('google-or-apple-auth')
        self.assertEqual(url, '/auth/login/google-or-apple/')
        self.assertEqual(resolve(url).func.view_class, GoogleAppleAuthView)

    # --- WebAuthn URLs ---
    def test_webauthn_register_start_url_resolves(self):
        """Test that the 'webauthn-register-start' URL resolves to the correct view."""
        url = reverse('webauthn-register-start')
        self.assertEqual(url, '/auth/webauthn/register/start/')
        self.assertEqual(resolve(url).func.view_class, StartWebAuthnRegistrationView)

    def test_webauthn_register_complete_url_resolves(self):
        """Test that the 'webauthn-register-complete' URL resolves to the correct view."""
        url = reverse('webauthn-register-complete')
        self.assertEqual(url, '/auth/webauthn/register/complete/')
        self.assertEqual(resolve(url).func.view_class, CompleteWebAuthnRegistrationView)

    def test_webauthn_login_start_url_resolves(self):
        """Test that the 'webauthn-login-start' URL resolves to the correct view."""
        url = reverse('webauthn-login-start')
        self.assertEqual(url, '/auth/webauthn/login/start/')
        self.assertEqual(resolve(url).func.view_class, StartWebAuthnAuthenticationView)

    def test_webauthn_login_complete_url_resolves(self):
        """Test that the 'webauthn-login-complete' URL resolves to the correct view."""
        url = reverse('webauthn-login-complete')
        self.assertEqual(url, '/auth/webauthn/login/complete/')
        self.assertEqual(resolve(url).func.view_class, CompleteWebAuthnAuthenticationView)

    def test_webauthn_credentials_list_url_resolves(self):
        """Test that the 'webauthn-credentials-list' URL resolves to the correct view."""
        url = reverse('webauthn-credentials-list')
        self.assertEqual(url, '/auth/webauthn/credentials/')
        self.assertEqual(resolve(url).func.view_class, ListWebAuthnCredentialsView)

    def test_webauthn_credential_delete_url_resolves(self):
        """Test that the 'webauthn-credential-delete' URL resolves to the correct view."""
        # Note: The pk is a placeholder for the primary key. We use a mock value.
        url = reverse('webauthn-credential-delete', args=[1])
        self.assertEqual(url, '/auth/webauthn/credentials/1/delete/')
        self.assertEqual(resolve(url).func.view_class, DeleteWebAuthnCredentialView)
    
    # --- ViewSet URLs ---
    def test_viewset_urls_exist(self):
        """Test that viewsets are correctly registered under the 'api/' prefix."""
        # Test a few examples from the router
        user_list_url = reverse('user-list')
        self.assertEqual(user_list_url, '/auth/api/users/')
        # self.assertEqual(resolve(user_list_url).func.view_class, UserViewSet)

        kyc_list_url = reverse('kyc-list')
        self.assertEqual(kyc_list_url, '/auth/api/kyc/')
        # self.assertEqual(resolve(kyc_list_url).func.view_class, KYCViewSet)

        referral_list_url = reverse('referral-list')
        self.assertEqual(referral_list_url, '/auth/api/referral/')
        # self.assertEqual(resolve(referral_list_url).func.view_class, ReferralViewSet)
