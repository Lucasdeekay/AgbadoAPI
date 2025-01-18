from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import transaction as db_transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from auth_app.views import get_user_from_token
from wallet_app.models import Wallet, Transaction, Withdrawal
from wallet_app.serializers import TransactionSerializer, WithdrawalSerializer
from auth_app.models import User


# 1. View to return wallet details and last 5 transactions
@method_decorator(csrf_exempt, name='dispatch')
class WalletDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = get_user_from_token(request)

            # Fetch wallet details
            wallet = Wallet.objects.get(user=user)
            wallet_data = {
                "balance": wallet.balance,
                "last_updated": wallet.updated_at,
            }

            # Fetch last 5 transactions
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
            transactions_data = TransactionSerializer(transactions, many=True).data

            return Response({
                "wallet": wallet_data,
                "recent_transactions": transactions_data
            }, status=status.HTTP_200_OK)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 2. View to return all transactions for the user
@method_decorator(csrf_exempt, name='dispatch')
class AllTransactionsView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = get_user_from_token(request)

            # Fetch all transactions for the user
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')
            transactions_data = TransactionSerializer(transactions, many=True).data

            return Response({"transactions": transactions_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 3. View to return details of a specific transaction
@method_decorator(csrf_exempt, name='dispatch')
class TransactionDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, transaction_id):
        try:
            user = get_user_from_token(request)

            # Fetch the specific transaction for the user
            transaction = Transaction.objects.get(Q(id=transaction_id) & Q(user=user))
            transaction_data = TransactionSerializer(transaction).data

            return Response({"transaction": transaction_data}, status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found or does not belong to this user."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid transaction ID."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class DepositView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = get_user_from_token(request)

            amount = request.data.get('amount')
            transaction_id = request.data.get('transaction_id')
            if not amount:
                return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)

            amount = Decimal(amount)
            if amount <= 0:
                return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the user's wallet
            wallet, created = Wallet.objects.get_or_create(user=user)

            # Save the transaction as a deposit
            with db_transaction.atomic():
                wallet.balance += amount
                wallet.save()

                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='Deposit',
                    transaction_id=transaction_id,
                    amount=amount,
                    status='Completed'
                )

            return Response({
                "message": "Deposit successful.",
                "wallet_balance": wallet.balance,
                "transaction": TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class WithdrawalRequestView(APIView):
    authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = get_user_from_token(request)

            bank_name = request.data.get('bank_name')
            account_number = request.data.get('account_number')
            amount = request.data.get('amount')
            transaction_id = request.data.get('transaction_id')

            # Input validation
            if not bank_name or not account_number or not amount:
                return Response({"error": "Bank name, account number, and amount are required."}, status=status.HTTP_400_BAD_REQUEST)

            amount = Decimal(amount)
            if amount <= 0:
                return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

            # Get user's wallet and check balance
            wallet = Wallet.objects.get(user=user)
            if wallet.balance < amount:
                return Response({"error": "Insufficient balance for withdrawal."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the withdrawal request
            with db_transaction.atomic():
                wallet.balance -= amount
                wallet.save()

                withdrawal = Withdrawal.objects.create(
                    user=user,
                    bank_name=bank_name,
                    account_number=account_number,
                    amount=amount,
                    status='Pending'
                )

                # Save a transaction record
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='Withdrawal',
                    transaction_id=transaction_id,
                    amount=amount,
                    status='Pending'
                )

            return Response({
                "message": "Withdrawal request submitted successfully.",
                "wallet_balance": wallet.balance,
                "withdrawal": WithdrawalSerializer(withdrawal).data,
                "transaction": TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)

        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
