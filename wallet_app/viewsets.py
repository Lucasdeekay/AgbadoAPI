"""
ViewSets for wallet app models.

This module contains ViewSets for handling CRUD operations on wallet-related models
including wallets, transactions, withdrawals, and banks with proper filtering and pagination.
"""

from rest_framework import serializers, viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction as db_transaction

from .models import Wallet, Transaction, Withdrawal, Bank
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    WithdrawalRequestSerializer,
    WithdrawalDetailSerializer,
    BankSerializer,
)
from .filters import (
    WalletFilter,
    TransactionFilter,
    WithdrawalFilter
)

# Import necessary modules for Paystack integration
import requests
import json
from django.conf import settings
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent page sizing across the API.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Wallet model.
    
    Provides read-only operations for wallets with user-specific filtering.
    Wallet creation and updates (balance) are handled internally.
    """
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = WalletFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filters the queryset to return only the wallet for the authenticated user.
        """
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-wallet')
    def my_wallet(self, request):
        """
        Custom action to retrieve the authenticated user's wallet.
        Automatically creates DVA if not present.
        """
        try:
            user_wallet, created = Wallet.objects.get_or_create(user=request.user)

            # Check if DVA exists, if not, attempt to create it
            if not user_wallet.dva_account_number:
                self._create_or_assign_dva(user_wallet)

            serializer = self.get_serializer(user_wallet)
            logger.info(f"Wallet details retrieved for user: {request.user.email}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving wallet for user {request.user.email}: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_or_assign_dva(self, wallet_instance):
        """
        Helper method to call Django backend endpoint to create/assign DVA.
        """
        # Ensure user has customer_code first
        if not wallet_instance.paystack_customer_code:
            try:
                self._create_paystack_customer(wallet_instance.user)
                # Re-fetch wallet instance after customer code is set by _create_paystack_customer
                wallet_instance.refresh_from_db()
            except Exception as e:
                logger.error(f"Error creating Paystack customer for user {wallet_instance.user.email}: {e}")
                return

        if not wallet_instance.dva_account_number and wallet_instance.paystack_customer_code:
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'customer': wallet_instance.paystack_customer_code,
                'preferred_bank': 'wema-bank',
                'first_name': wallet_instance.user.first_name,
                'last_name': wallet_instance.user.last_name,
                'phone': wallet_instance.user.phone,
            }

            try:
                response = requests.post(f"{settings.PAYSTACK_API_BASE_URL}/dedicated_account", headers=headers, json=payload)
                response.json()

                if response.status_code == 200 and response.json().get('status'):
                    dva_data = response.json()['data']
                    wallet_instance.dva_account_number = dva_data['account_number']
                    wallet_instance.dva_account_name = dva_data['account_name']
                    wallet_instance.dva_bank_name = dva_data['bank']['name']
                    wallet_instance.dva_assigned_at = timezone.now()
                    wallet_instance.save(update_fields=['dva_account_number', 'dva_account_name', 'dva_bank_name', 'dva_assigned_at'])
                    logger.info(f"DVA created for user: {wallet_instance.user.email}")
                else:
                    error_message = response.json().get('message', 'Unknown error from Paystack DVA creation.')
                    logger.error(f"Paystack DVA creation failed for user {wallet_instance.user.email}: {error_message}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network/API error during DVA creation for user {wallet_instance.user.email}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during DVA creation for user {wallet_instance.user.email}: {e}")

    def _create_paystack_customer(self, user_instance):
        """
        Helper method to create a Paystack customer for the user if they don't have a code.
        """
        if user_instance.wallet.paystack_customer_code:
            return

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'email': user_instance.email,
            'first_name': user_instance.first_name,
            'last_name': user_instance.last_name,
            'phone': getattr(user_instance, 'phone', '')
        }

        try:
            response = requests.post(f"{settings.PAYSTACK_API_BASE_URL}/customer", headers=headers, json=payload)
            response.raise_for_status()

            paystack_customer_data = response.json()
            if paystack_customer_data.get('status'):
                customer_code = paystack_customer_data['data']['customer_code']
                user_instance.wallet.paystack_customer_code = customer_code
                user_instance.wallet.save(update_fields=['paystack_customer_code'])
                logger.info(f"Paystack customer created for {user_instance.email}: {customer_code}")
            else:
                error_message = paystack_customer_data.get('message', 'Failed to create Paystack customer.')
                logger.error(f"Paystack customer creation failed for {user_instance.email}: {error_message}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network/API error during Paystack customer creation for {user_instance.email}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Paystack customer creation for {user_instance.email}: {e}")


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Transaction model.
    
    Provides read-only operations for transactions with user-specific filtering.
    Transaction creation is handled by webhook or internal logic.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TransactionFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filters the queryset to return only transactions for the authenticated user.
        """
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')


class WithdrawalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Withdrawal model.
    
    Provides CRUD operations for withdrawals with user-specific filtering.
    """
    queryset = Withdrawal.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = WithdrawalFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filters the queryset to return only withdrawals for the authenticated user.
        """
        return Withdrawal.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        """
        Returns the appropriate serializer based on the action.
        """
        if self.action == 'create':
            return WithdrawalRequestSerializer
        return WithdrawalDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Handles the creation of a new withdrawal request.
        Validates amount, checks user balance, then initiates Paystack transfer.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = request.user
            amount_to_withdraw = serializer.validated_data['amount']
            bank_name = serializer.validated_data['bank_name']
            account_number = serializer.validated_data['account_number']

            # Ensure atomicity for balance deduction
            with db_transaction.atomic():
                user_wallet = Wallet.objects.select_for_update().get(user=user)

                if user_wallet.balance < amount_to_withdraw:
                    return Response(
                        {"detail": "Insufficient balance for withdrawal."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Deduct from balance immediately to prevent double spending
                user_wallet.balance -= amount_to_withdraw
                user_wallet.save(update_fields=['balance'])

                # Create the Withdrawal record with 'Pending' status
                withdrawal_instance = Withdrawal.objects.create(
                    user=user,
                    bank_name=bank_name,
                    account_number=account_number,
                    amount=amount_to_withdraw,
                    status='Pending',
                )

                # Create a corresponding Transaction for this withdrawal
                Transaction.objects.create(
                    user=user,
                    transaction_type='Withdrawal',
                    amount=amount_to_withdraw,
                    status='Pending',
                )

            # Now, try to initiate the transfer with Paystack
            try:
                paystack_response = self._initiate_paystack_transfer(
                    user,
                    amount_to_withdraw,
                    bank_name,
                    account_number,
                    withdrawal_instance
                )

                if paystack_response and paystack_response.get('status'):
                    # Paystack transfer initiated successfully
                    transfer_data = paystack_response['data']
                    withdrawal_instance.paystack_transfer_reference = transfer_data['reference']
                    withdrawal_instance.paystack_transfer_id = transfer_data['id']
                    withdrawal_instance.status = 'Processing'
                    withdrawal_instance.save(update_fields=['paystack_transfer_reference', 'paystack_transfer_id', 'status'])

                    # Update the related transaction's reference and status
                    Transaction.objects.filter(
                        user=user,
                        transaction_type='Withdrawal',
                        amount=amount_to_withdraw,
                        status='Pending'
                    ).update(reference=transfer_data['reference'], status='Processing')

                    logger.info(f"Withdrawal initiated successfully for user: {user.email}")
                    headers = self.get_success_headers(serializer.data)
                    return Response(
                        WithdrawalDetailSerializer(withdrawal_instance).data,
                        status=status.HTTP_202_ACCEPTED,
                        headers=headers
                    )
                else:
                    # Paystack transfer initiation failed
                    error_message = paystack_response.get('message', 'Failed to initiate Paystack transfer.')
                    logger.error(f"Paystack transfer initiation failed: {error_message}")

                    # Rollback balance deduction if transfer failed at this stage
                    user_wallet.balance += amount_to_withdraw
                    user_wallet.save(update_fields=['balance'])
                    withdrawal_instance.status = 'Failed'
                    withdrawal_instance.failure_reason = f"Paystack initiation failed: {error_message}"
                    withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                    # Update the corresponding transaction
                    Transaction.objects.filter(
                        user=user,
                        transaction_type='Withdrawal',
                        amount=amount_to_withdraw,
                        status='Pending'
                    ).update(status='Failed', reference=f"FAILED-{timezone.now().timestamp()}")

                    return Response(
                        {"detail": f"Withdrawal request failed: {error_message}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except requests.exceptions.RequestException as e:
                # Network or API call error
                logger.error(f"Network error initiating Paystack transfer: {e}")
                # Rollback balance deduction
                user_wallet.balance += amount_to_withdraw
                user_wallet.save(update_fields=['balance'])
                withdrawal_instance.status = 'Failed'
                withdrawal_instance.failure_reason = f"Network/API error: {e}"
                withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                # Update the corresponding transaction
                Transaction.objects.filter(
                    user=user,
                    transaction_type='Withdrawal',
                    amount=amount_to_withdraw,
                    status='Pending'
                ).update(status='Failed', reference=f"NETWORK-FAILED-{timezone.now().timestamp()}")

                return Response(
                    {"detail": "A network error occurred while processing your withdrawal. Please try again later."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as e:
                # Any other unexpected error
                logger.error(f"Unexpected error during withdrawal: {e}")
                # Rollback balance deduction
                user_wallet.balance += amount_to_withdraw
                user_wallet.save(update_fields=['balance'])
                withdrawal_instance.status = 'Failed'
                withdrawal_instance.failure_reason = f"Unexpected error: {e}"
                withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                # Update the corresponding transaction
                Transaction.objects.filter(
                    user=user,
                    transaction_type='Withdrawal',
                    amount=amount_to_withdraw,
                    status='Pending'
                ).update(status='Failed', reference=f"UNEXPECTED-FAILED-{timezone.now().timestamp()}")

                return Response(
                    {"detail": "An unexpected error occurred while processing your withdrawal."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error creating withdrawal: {str(e)}")
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _initiate_paystack_transfer(self, user, amount, bank_name, account_number, withdrawal_instance):
        """
        Helper method to handle Paystack transfer initiation.
        Returns Paystack response data if successful, None otherwise.
        """
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        # Step 1: Resolve Account Number
        try:
            resolve_response = requests.get(
                f"{settings.PAYSTACK_API_BASE_URL}/bank/resolve?account_number={account_number}&bank_code={self._get_bank_code(bank_name)}",
                headers=headers
            )
            resolve_response.raise_for_status()
            resolved_data = resolve_response.json()
            if resolved_data.get('status'):
                resolved_account_name = resolved_data['data']['account_name']
                withdrawal_instance.account_name = resolved_account_name
                withdrawal_instance.save(update_fields=['account_name'])
            else:
                raise Exception(f"Account resolution failed: {resolved_data.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Account resolution failed for {account_number}, {bank_name}: {e}")
            raise serializers.ValidationError(f"Could not verify bank account details: {e}")

        # Step 2: Create Transfer Recipient
        recipient_payload = {
            'type': 'nuban',
            'name': resolved_account_name,
            'description': f"Withdrawal for {user.email}",
            'account_number': account_number,
            'bank_code': self._get_bank_code(bank_name),
            'currency': 'NGN'
        }
        try:
            recipient_response = requests.post(
                f"{settings.PAYSTACK_API_BASE_URL}/transferrecipient",
                headers=headers,
                json=recipient_payload
            )
            recipient_response.raise_for_status()
            recipient_data = recipient_response.json()
            if recipient_data.get('status'):
                recipient_code = recipient_data['data']['recipient_code']
                withdrawal_instance.paystack_recipient_code = recipient_code
                withdrawal_instance.save(update_fields=['paystack_recipient_code'])
            else:
                raise Exception(f"Failed to create transfer recipient: {recipient_data.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error creating transfer recipient: {e}")
            raise serializers.ValidationError(f"Could not set up transfer: {e}")

        # Step 3: Initiate Transfer
        transfer_payload = {
            'source': 'balance',
            'amount': int(amount * 100),
            'recipient': withdrawal_instance.paystack_recipient_code,
            'reason': f"Withdrawal for {user.email}",
            'reference': f"WITHDRAWAL-{user.id}-{timezone.now().timestamp()}-{withdrawal_instance.id}"
        }

        try:
            transfer_response = requests.post(
                f"{settings.PAYSTACK_API_BASE_URL}/transfer",
                headers=headers,
                json=transfer_payload
            )
            transfer_response.raise_for_status()
            return transfer_response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack transfer API error: {e}")
            raise

    def _get_bank_code(self, bank_name):
        """
        Helper to map bank name to Paystack bank code.
        """
        bank_codes = {
            'wema bank': '035',
            'zenith bank': '057',
            'guaranty trust bank': '058',
            'access bank': '044',
            'first bank of nigeria': '011',
        }
        return bank_codes.get(bank_name.lower(), None)


class BankViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Bank model.
    
    Provides read-only operations for banks with public access.
    """
    queryset = Bank.objects.filter(is_active=True)
    serializer_class = BankSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def fetch_from_paystack(self, request):
        """
        Custom action to fetch and update the list of banks from Paystack.
        Requires admin privileges.
        """
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(f"{settings.PAYSTACK_API_BASE_URL}/bank", headers=headers)
            response.raise_for_status()
            bank_data = response.json()

            if bank_data.get('status'):
                fetched_banks = bank_data['data']
                updated_count = 0
                created_count = 0

                for bank_info in fetched_banks:
                    bank_obj, created = Bank.objects.update_or_create(
                        code=bank_info['code'],
                        defaults={
                            'name': bank_info['name'],
                            'slug': bank_info['slug'],
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                # Deactivate any banks that are no longer returned by Paystack
                paystack_codes = {bank['code'] for bank in fetched_banks}
                db_active_codes = set(Bank.objects.filter(is_active=True).values_list('code', flat=True))
                to_deactivate_codes = db_active_codes - paystack_codes
                deactivated_count = Bank.objects.filter(code__in=to_deactivate_codes).update(is_active=False)

                logger.info(f"Banks list updated: {created_count} created, {updated_count} updated, {deactivated_count} deactivated")
                return Response({
                    "message": "Banks list updated successfully.",
                    "created": created_count,
                    "updated": updated_count,
                    "deactivated": deactivated_count
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"message": bank_data.get('message', 'Failed to fetch banks from Paystack.')}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Paystack bank API: {e}")
            return Response(
                {"message": f"Error connecting to Paystack bank API: {e}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error updating banks: {e}")
            return Response(
                {"message": f"An unexpected error occurred: {e}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

