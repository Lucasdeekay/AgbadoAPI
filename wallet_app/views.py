from decimal import Decimal
import hmac
import hashlib
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
from django.http import HttpResponse
from django.utils import timezone # For precise timestamps
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from auth_app.views import get_user_from_token # Assuming this correctly fetches user from token
from notification_app.models import Notification
from wallet_app.models import Wallet, Transaction, Withdrawal, Bank
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
    Retrieves the bank code from the local database.
    Assumes the Bank model is populated via the fetch_from_paystack endpoint.
    """
    try:
        # Try to find by exact name or slug
        bank = Bank.objects.get(Q(name__iexact=bank_name) | Q(slug__iexact=bank_name), is_active=True)
        return bank.code
    except Bank.DoesNotExist:
        # Fallback to crude match for common variations if needed, or raise error
        # It's better to guide the user to select from a list
        print(f"Bank '{bank_name}' not found in local database or not active.")
        # You might still have a small, hardcoded fallback for well-known banks
        # if your list isn't always fresh, but rely on DB first.
        bank_codes_fallback = {
            'wema bank': '035', 'zenith bank': '057', 'gtbank': '058', # etc.
        }
        return bank_codes_fallback.get(bank_name.lower(), None)
    except Exception as e:
        print(f"Error getting bank code for {bank_name}: {e}")
        return None


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
        


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    authentication_classes = [] # No authentication for webhooks
    permission_classes = []     # No permissions for webhooks

    def post(self, request, *args, **kwargs):
        # 1. Verify Webhook Signature
        paystack_signature = request.headers.get('x-paystack-signature')
        if not paystack_signature:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="No X-Paystack-Signature header.")

        # Get raw request body (important for signature verification)
        raw_payload = request.body.decode('utf-8')

        # Hash the payload with your secret key
        digest = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            raw_payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        if digest != paystack_signature:
            print("Webhook signature mismatch. Potential tampering detected.")
            return HttpResponse(status=status.HTTP_403_FORBIDDEN, content="Invalid webhook signature.")

        # 2. Parse the Event Data
        try:
            event = json.loads(raw_payload)
        except json.JSONDecodeError:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Invalid JSON payload.")

        event_type = event.get('event')
        event_data = event.get('data')

        if not event_type or not event_data:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST, content="Invalid event data structure.")

        # Paystack expects a 200 OK response quickly, even if processing takes time.
        # For complex logic, you'd send 200 OK immediately and offload processing to a task queue.
        # For this example, we'll process synchronously.
        try:
            if event_type == 'charge.success':
                self._handle_charge_success(event_data)
            elif event_type == 'transfer.success':
                self._handle_transfer_success(event_data)
            elif event_type == 'transfer.failed':
                self._handle_transfer_failed(event_data)
            elif event_type == 'transfer.reversed':
                self._handle_transfer_reversed(event_data)
            # Add other event types if necessary (e.g., invoice.create, subscription.update)
            else:
                print(f"Unhandled Paystack event type: {event_type}")

            return HttpResponse(status=status.HTTP_200_OK) # Acknowledge receipt
        except Exception as e:
            # Log the error, but still return 200 to Paystack to prevent retries
            # For debugging, you might temporarily return 500, but in production, 200 is safer.
            print(f"Error processing Paystack webhook event {event_type}: {e}")
            return HttpResponse(status=status.HTTP_200_OK) # Still return 200 to Paystack


    def _handle_charge_success(self, data):
        """
        Handles successful deposit events (e.g., from Dedicated Virtual Accounts).
        """
        reference = data.get('reference')
        amount_kobo = data.get('amount') # Amount in kobo/pesewas
        status = data.get('status')
        customer_email = data.get('customer', {}).get('email')
        paystack_transaction_id = data.get('id')
        paid_at = data.get('paid_at') # Payment timestamp

        if status != 'success':
            print(f"Charge not successful for reference {reference}, status: {status}")
            return

        amount = Decimal(amount_kobo) / 100 # Convert kobo to your currency unit

        with db_transaction.atomic():
            # Check for idempotency: Has this transaction already been processed?
            if Transaction.objects.filter(reference=reference, status='Completed').exists():
                print(f"Deposit with reference {reference} already processed. Skipping.")
                return

            try:
                # Find user by email (or by customer_code if stored on User model directly)
                user = User.objects.get(email=customer_email)
                wallet = Wallet.objects.select_for_update().get(user=user)

                wallet.balance += amount
                wallet.save(update_fields=['balance'])

                transaction, created = Transaction.objects.get_or_create(
                    reference=reference, # Use reference for uniqueness
                    defaults={
                        'user': user,
                        'transaction_type': 'Deposit',
                        'amount': amount,
                        'status': 'Completed',
                        'paystack_transaction_id': paystack_transaction_id,
                        'created_at': timezone.datetime.fromisoformat(paid_at.replace('Z', '+00:00')) if paid_at else timezone.now(),
                    }
                )
                if not created:
                    # If transaction already existed but wasn't 'Completed' (e.g., failed retry)
                    transaction.status = 'Completed'
                    transaction.paystack_transaction_id = paystack_transaction_id
                    transaction.save(update_fields=['status', 'paystack_transaction_id'])

                Notification.objects.create(
                    user=user,
                    title="Deposit Successful",
                    message=f"A deposit of {amount} has been successfully added to your wallet. Ref: {reference}"
                )
                print(f"Successfully processed deposit for {user.email}, amount {amount}, ref {reference}")

            except User.DoesNotExist:
                print(f"User not found for email: {customer_email}. Cannot process deposit {reference}.")
                # Handle this: maybe create a user? Log a critical error?
            except Wallet.DoesNotExist:
                print(f"Wallet not found for user: {customer_email}. Cannot process deposit {reference}.")
                # This should ideally not happen if you create wallets with users
            except Exception as e:
                print(f"Error handling charge.success for {reference}: {e}")
                raise # Re-raise to ensure transaction rollback if within atomic block

    def _handle_transfer_success(self, data):
        """
        Handles successful withdrawal (transfer) events.
        """
        reference = data.get('reference')
        amount_kobo = data.get('amount')
        paystack_transfer_id = data.get('id')

        amount = Decimal(amount_kobo) / 100

        with db_transaction.atomic():
            try:
                # Find the corresponding Withdrawal request
                withdrawal = Withdrawal.objects.select_for_update().get(
                    paystack_transfer_reference=reference
                )

                if withdrawal.status == 'Completed':
                    print(f"Withdrawal {reference} already marked as completed. Skipping.")
                    return

                withdrawal.status = 'Completed'
                withdrawal.updated_at = timezone.now()
                withdrawal.save(update_fields=['status', 'updated_at'])

                # Update the corresponding Transaction
                transaction = Transaction.objects.get(
                    user=withdrawal.user,
                    transaction_type='Withdrawal',
                    reference=reference # Match by the same reference
                )
                transaction.status = 'Completed'
                transaction.updated_at = timezone.now()
                transaction.save(update_fields=['status', 'updated_at'])

                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal Completed",
                    message=f"Your withdrawal of {amount} has been successfully processed."
                )
                print(f"Successfully processed successful transfer for {reference}")

            except Withdrawal.DoesNotExist:
                print(f"Withdrawal request with reference {reference} not found. Could not update status.")
            except Transaction.DoesNotExist:
                print(f"Transaction for withdrawal {reference} not found. Data inconsistency.")
            except Exception as e:
                print(f"Error handling transfer.success for {reference}: {e}")
                raise

    def _handle_transfer_failed(self, data):
        """
        Handles failed withdrawal (transfer) events. Funds are NOT returned by Paystack.
        This means the funds were deducted from your Paystack balance but didn't reach the recipient.
        You might need to manually reconcile or contact Paystack support.
        From a user's wallet perspective, their balance was already reduced, and it should remain so.
        """
        reference = data.get('reference')
        fail_reason = data.get('transfer_code_reason') or data.get('status') or 'Unknown reason'
        amount_kobo = data.get('amount')
        
        amount = Decimal(amount_kobo) / 100

        with db_transaction.atomic():
            try:
                withdrawal = Withdrawal.objects.select_for_update().get(
                    paystack_transfer_reference=reference
                )

                if withdrawal.status == 'Failed':
                    print(f"Withdrawal {reference} already marked as failed. Skipping.")
                    return

                withdrawal.status = 'Failed'
                withdrawal.failure_reason = f"Paystack transfer failed: {fail_reason}"
                withdrawal.updated_at = timezone.now()
                withdrawal.save(update_fields=['status', 'failure_reason', 'updated_at'])

                transaction = Transaction.objects.get(
                    user=withdrawal.user,
                    transaction_type='Withdrawal',
                    reference=reference
                )
                transaction.status = 'Failed'
                transaction.updated_at = timezone.now()
                transaction.save(update_fields=['status', 'updated_at'])

                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal Failed",
                    message=f"Your withdrawal of {amount} failed. Reason: {fail_reason}. Please contact support."
                )
                print(f"Processed failed transfer for {reference}, reason: {fail_reason}")

            except Withdrawal.DoesNotExist:
                print(f"Withdrawal request with reference {reference} not found for failed event.")
            except Transaction.DoesNotExist:
                print(f"Transaction for failed withdrawal {reference} not found. Data inconsistency.")
            except Exception as e:
                print(f"Error handling transfer.failed for {reference}: {e}")
                raise

    def _handle_transfer_reversed(self, data):
        """
        Handles reversed withdrawal (transfer) events.
        This means the funds were reversed back to YOUR Paystack balance.
        Crucially, you MUST credit the user's wallet back.
        """
        reference = data.get('reference')
        amount_kobo = data.get('amount')
        reverse_reason = data.get('message') or 'Unknown reason'

        amount = Decimal(amount_kobo) / 100

        with db_transaction.atomic():
            try:
                withdrawal = Withdrawal.objects.select_for_update().get(
                    paystack_transfer_reference=reference
                )

                if withdrawal.status == 'Reversed':
                    print(f"Withdrawal {reference} already marked as reversed. Skipping.")
                    return

                # Update Withdrawal status
                withdrawal.status = 'Reversed'
                withdrawal.failure_reason = f"Paystack transfer reversed: {reverse_reason}"
                withdrawal.updated_at = timezone.now()
                withdrawal.save(update_fields=['status', 'failure_reason', 'updated_at'])

                # Credit user's wallet back
                user_wallet = Wallet.objects.select_for_update().get(user=withdrawal.user)
                user_wallet.balance += amount
                user_wallet.save(update_fields=['balance'])
                print(f"Credited wallet of {user_wallet.user.email} with {amount} due to reversed transfer {reference}.")

                # Update the corresponding Transaction
                transaction = Transaction.objects.get(
                    user=withdrawal.user,
                    transaction_type='Withdrawal',
                    reference=reference
                )
                transaction.status = 'Reversed'
                transaction.updated_at = timezone.now()
                transaction.save(update_fields=['status', 'updated_at'])

                # Create a new deposit transaction to clearly show funds return
                Transaction.objects.create(
                    user=withdrawal.user,
                    transaction_type='Deposit',
                    amount=amount,
                    status='Completed',
                    reference=f"REVERSED-DEPOSIT-{reference}", # New unique ref for the return
                    # Link to original withdrawal if needed
                )

                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal Reversed & Funds Returned",
                    message=f"Your withdrawal of {amount} was reversed. The funds have been returned to your wallet. Reason: {reverse_reason}"
                )
                print(f"Processed reversed transfer for {reference}, reason: {reverse_reason}. Funds returned to wallet.")

            except Withdrawal.DoesNotExist:
                print(f"Withdrawal request with reference {reference} not found for reversed event.")
            except Transaction.DoesNotExist:
                print(f"Transaction for reversed withdrawal {reference} not found. Data inconsistency.")
            except Wallet.DoesNotExist:
                print(f"Wallet for user {withdrawal.user.email} not found for reversed transfer {reference}. Critical error.")
            except Exception as e:
                print(f"Error handling transfer.reversed for {reference}: {e}")
                raise

