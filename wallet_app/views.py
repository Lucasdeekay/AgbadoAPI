from decimal import Decimal
import os
import requests
import json # Import json for Paystack response parsing

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import transaction as db_transaction
from django.utils import timezone # For precise timestamps

from auth_app.views import get_user_from_token # Assuming this correctly fetches user from token
from notification_app.models import Notification
from wallet_app.models import Wallet, Transaction, Withdrawal
from wallet_app.serializers import (
    WalletSerializer, # Use WalletSerializer for full wallet details
    TransactionSerializer,
    WithdrawalRequestSerializer, # For user input
    WithdrawalDetailSerializer,   # For displaying processed withdrawals
)
from auth_app.models import User # Ensure User model is correctly imported

# Paystack Configuration
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_API_BASE_URL = "https://api.paystack.co"

# Helper function to get bank code (ideally from a cached DB table or Paystack's /bank API)
def _get_bank_code(bank_name):
    """
    Helper to map bank name to Paystack bank code.
    In a real application, you'd fetch this dynamically from Paystack's /bank endpoint
    and cache it, or maintain a secure list in your database.
    """
    bank_codes = {
        'wema bank': '035',
        'zenith bank': '057',
        'guaranty trust bank': '058',
        'access bank': '044',
        'first bank of nigeria': '011',
        'union bank of nigeria': '032',
        'fidelity bank': '070',
        'united bank for africa': '033',
        'stanbic ibtc bank': '221',
        'sterling bank': '232',
        'gtbank': '058', # Common alias
        'access': '044',
        'fbn': '011',
        # ... add more common banks and their codes
    }
    return bank_codes.get(bank_name.lower(), None) # Convert to lowercase for matching


# 1. View to return wallet details and last 5 transactions
class WalletDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Enable permission

    def get(self, request):
        try:
            user = get_user_from_token(request) # Ensure this correctly returns a User object

            # Fetch wallet details - create if it doesn't exist (e.g., for new users)
            wallet, created = Wallet.objects.get_or_create(user=user)

            # Use the WalletSerializer for comprehensive details
            wallet_data = WalletSerializer(wallet).data

            # Fetch last 5 transactions
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
            transactions_data = TransactionSerializer(transactions, many=True).data

            return Response({
                "wallet": wallet_data,
                "recent_transactions": transactions_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 2. View to return all transactions for the user
class AllTransactionsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Enable permission

    def get(self, request):
        try:
            user = get_user_from_token(request)

            # Fetch all transactions for the user
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')
            transactions_data = TransactionSerializer(transactions, many=True).data

            return Response({"transactions": transactions_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Enable permission

    def get(self, request, pk): # Use 'pk' (primary key) for detail view conventions
        try:
            user = get_user_from_token(request)

            # Fetch the specific transaction for the user
            # Use get_object_or_404 for cleaner error handling
            transaction = Transaction.objects.get(Q(id=pk) & Q(user=user))
            transaction_data = TransactionSerializer(transaction).data

            return Response({"transaction": transaction_data}, status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            return Response({"message": "Transaction not found or does not belong to this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e: # Catch other potential errors like invalid UUID if pk is UUIDField
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- DEPOSIT HANDLING (REMOVED DIRECT USER INITIATION) ---
# Direct user-initiated DepositView for `POST` is removed.
# Deposits via Dedicated Virtual Accounts are handled by Paystack webhooks.
# The client only needs to retrieve the DVA details from WalletDetailsView.


class WithdrawalRequestView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Enable permission

    def post(self, request):
        user = get_user_from_token(request)

        # Use the dedicated serializer for input validation
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Will raise 400 Bad Request if invalid

        amount_to_withdraw = serializer.validated_data['amount']
        bank_name = serializer.validated_data['bank_name']
        account_number = serializer.validated_data['account_number']

        try:
            # Ensure atomicity for balance deduction and record creation
            with db_transaction.atomic():
                user_wallet = Wallet.objects.select_for_update().get(user=user)

                if user_wallet.balance < amount_to_withdraw:
                    return Response(
                        {"message": "Insufficient balance for withdrawal."},
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
                    status='Pending', # Initial status before Paystack interaction
                )

                # Create a corresponding Transaction for this withdrawal
                transaction_instance = Transaction.objects.create(
                    user=user,
                    transaction_type='Withdrawal',
                    amount=amount_to_withdraw,
                    status='Pending', # Transaction status linked to withdrawal status
                    # reference will be updated after Paystack transfer initiation
                )

            # Now, attempt to initiate the transfer with Paystack
            paystack_response = self._initiate_paystack_transfer(
                user,
                amount_to_withdraw,
                bank_name,
                account_number,
                withdrawal_instance # Pass instance to update its Paystack IDs
            )

            if paystack_response and paystack_response.get('status'):
                # Paystack transfer initiated successfully (status is 'pending' on Paystack's side)
                transfer_data = paystack_response['data']
                withdrawal_instance.paystack_transfer_reference = transfer_data['reference']
                withdrawal_instance.paystack_transfer_id = transfer_data['id']
                withdrawal_instance.status = 'Processing' # Mark as processing in your system
                withdrawal_instance.save(update_fields=['paystack_transfer_reference', 'paystack_transfer_id', 'status'])

                # Update the related transaction's reference and status
                transaction_instance.reference = transfer_data['reference']
                transaction_instance.status = 'Processing'
                transaction_instance.save(update_fields=['reference', 'status'])

                Notification.objects.create(
                    user=user,
                    title="Withdrawal Initiated",
                    message=f"Your withdrawal of {amount_to_withdraw} is being processed. It may take some time to reflect."
                )

                return Response(
                    WithdrawalDetailSerializer(withdrawal_instance).data, # Use Detail serializer for response
                    status=status.HTTP_202_ACCEPTED, # 202 Accepted, as processing is ongoing
                )
            else:
                # Paystack transfer initiation failed (e.g., invalid recipient, bank issues)
                error_message = paystack_response.get('message', 'Failed to initiate Paystack transfer.')
                print(f"Paystack transfer initiation failed: {error_message}")

                # Rollback balance deduction as transfer failed to start
                user_wallet.balance += amount_to_withdraw
                user_wallet.save(update_fields=['balance'])
                withdrawal_instance.status = 'Failed'
                withdrawal_instance.failure_reason = f"Paystack initiation failed: {error_message}"
                withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                transaction_instance.status = 'Failed'
                transaction_instance.reference = f"FAILED-INIT-{timezone.now().timestamp()}" # Unique failed ref
                transaction_instance.save(update_fields=['status', 'reference'])

                Notification.objects.create(
                    user=user,
                    title="Withdrawal Failed",
                    message=f"Your withdrawal of {amount_to_withdraw} failed to initiate. Funds have been returned to your wallet. Reason: {error_message}"
                )

                return Response(
                    {"message": f"Withdrawal request failed: {error_message}", "funds_returned": True},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Wallet.DoesNotExist:
            return Response({"message": "Wallet not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.RequestException as e:
            # Catch network errors during API calls to Paystack
            print(f"Network error initiating Paystack transfer: {e}")

            # Rollback balance deduction
            try:
                user_wallet.balance += amount_to_withdraw
                user_wallet.save(update_fields=['balance'])
                withdrawal_instance.status = 'Failed'
                withdrawal_instance.failure_reason = f"Network/API error: {e}"
                withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                transaction_instance.status = 'Failed'
                transaction_instance.reference = f"NETWORK-ERR-{timezone.now().timestamp()}"
                transaction_instance.save(update_fields=['status', 'reference'])

                Notification.objects.create(
                    user=user,
                    title="Withdrawal Error",
                    message=f"A network error occurred during your withdrawal of {amount_to_withdraw}. Funds have been returned to your wallet. Please try again."
                )
                return Response(
                    {"message": "A network error occurred while processing your withdrawal. Funds returned to wallet. Please try again later."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as rollback_e:
                # If rollback itself fails, log a critical error
                print(f"CRITICAL: Failed to rollback wallet balance for user {user.id} after transfer initiation error: {rollback_e}")
                return Response(
                    {"message": "A critical error occurred. Please contact support."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error during withdrawal request: {e}")
            # Attempt to rollback balance deduction
            try:
                user_wallet.balance += amount_to_withdraw
                user_wallet.save(update_fields=['balance'])
                withdrawal_instance.status = 'Failed'
                withdrawal_instance.failure_reason = f"Unexpected error: {e}"
                withdrawal_instance.save(update_fields=['status', 'failure_reason'])

                transaction_instance.status = 'Failed'
                transaction_instance.reference = f"UNEXPECTED-ERR-{timezone.now().timestamp()}"
                transaction_instance.save(update_fields=['status', 'reference'])

                Notification.objects.create(
                    user=user,
                    title="Withdrawal Error",
                    message=f"An unexpected error occurred during your withdrawal of {amount_to_withdraw}. Funds have been returned to your wallet. Please try again."
                )
                return Response(
                    {"message": "An unexpected error occurred while processing your withdrawal. Funds returned to wallet."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as rollback_e:
                print(f"CRITICAL: Failed to rollback wallet balance for user {user.id} after unexpected error: {rollback_e}")
                return Response(
                    {"message": "A critical error occurred. Please contact support."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def _initiate_paystack_transfer(self, user, amount, bank_name, account_number, withdrawal_instance):
        """
        Helper method to handle Paystack transfer initiation steps:
        1. Resolve Account Number
        2. Create/Get Transfer Recipient
        3. Initiate Transfer
        """
        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        # Step 1: Resolve Account Number
        bank_code = _get_bank_code(bank_name)
        if not bank_code:
            raise ValueError(f"Invalid or unsupported bank name: {bank_name}")

        try:
            resolve_url = f"{PAYSTACK_API_BASE_URL}/bank/resolve?account_number={account_number}&bank_code={bank_code}"
            resolve_response = requests.get(resolve_url, headers=headers)
            resolve_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            resolved_data = resolve_response.json()

            if resolved_data.get('status'):
                resolved_account_name = resolved_data['data']['account_name']
                # Update withdrawal instance with verified account name
                withdrawal_instance.account_name = resolved_account_name
                # Note: We save the instance at the end of the main try block's success path
                # so intermediate saves are handled there for atomic operations.
            else:
                raise Exception(f"Account resolution failed: {resolved_data.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Paystack Account Resolution API error: {e}")
        except Exception as e:
            raise Exception(f"Account resolution error: {e}")

        # Step 2: Create or retrieve Transfer Recipient
        # For robustness, you might want to check if a recipient for this account_number already exists
        # within your system or on Paystack before creating a new one every time.
        # For this example, we'll create one if it doesn't exist, or reuse by getting it.
        # A more robust solution involves storing recipient_code on your User or a separate model.
        recipient_code = None
        # You could try to list existing recipients and find a match for reuse
        # Or, just create a new one each time for simplicity in this example, Paystack handles duplicates well.
        
        recipient_payload = {
            'type': 'nuban',
            'name': resolved_account_name, # Use the verified name
            'description': f"Withdrawal for {user.email}",
            'account_number': account_number,
            'bank_code': bank_code,
            'currency': 'NGN' # Ensure this matches your Paystack account currency
        }
        try:
            recipient_response = requests.post(
                f"{PAYSTACK_API_BASE_URL}/transferrecipient",
                headers=headers,
                json=recipient_payload
            )
            recipient_response.raise_for_status()
            recipient_data = recipient_response.json()

            if recipient_data.get('status'):
                recipient_code = recipient_data['data']['recipient_code']
                withdrawal_instance.paystack_recipient_code = recipient_code
                # Note: We save the instance at the end of the main try block's success path
            else:
                raise Exception(f"Failed to create transfer recipient: {recipient_data.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Paystack Transfer Recipient API error: {e}")
        except Exception as e:
            raise Exception(f"Error creating transfer recipient: {e}")

        # Step 3: Initiate Transfer
        transfer_payload = {
            'source': 'balance', # Transfers from your Paystack balance
            'amount': int(amount * 100), # Amount in kobo/pesewas
            'recipient': recipient_code,
            'reason': f"Withdrawal for {user.email} - {account_number}",
            'reference': f"WITHDRAWAL-{user.id}-{withdrawal_instance.id}-{timezone.now().timestamp()}" # Highly unique reference
        }

        try:
            transfer_response = requests.post(
                f"{PAYSTACK_API_BASE_URL}/transfer",
                headers=headers,
                json=transfer_payload
            )
            transfer_response.raise_for_status()
            return transfer_response.json() # Returns Paystack's response for further processing
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Paystack Transfer Initiation API error: {e}")
        except Exception as e:
            raise Exception(f"Error initiating Paystack transfer: {e}")