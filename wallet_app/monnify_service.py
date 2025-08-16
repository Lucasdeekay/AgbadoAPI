"""
- Authentication
- Creating reserved accounts
- Fetching account details
- Validating transactions
- Initiating disbursements
- Checking disbursement status

---

*🐍 MonnifyService Class (Python)*
"""
# monnify_service.py
import requests
import base64
import hashlib

class MonnifyService:
    def __init__(self, api_key, secret_key, contract_code, base_url=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.contract_code = contract_code
        self.base_url = base_url or "https://api.monnify.com/api/v1"
        self.access_token = None

    def authenticate(self):
        """
        Authenticate with Monnify API and store access token.
        """
        auth_string = f"{self.api_key}:{self.secret_key}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}"
}

        response = requests.post(f"{self.base_url}/auth/login", headers=headers)
        response.raise_for_status()
        self.access_token = response.json()['responseBody']['accessToken']
        return self.access_token

    def _get_headers(self):
        """
        Helper method to return headers with Bearer token.
        """
        if not self.access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
}

    def create_reserved_account(self, customer):
        """
        Create a reserved virtual account for a unique customer.

:param customer: dict with keys 'reference', 'name', 'email'
:return: dict with account details
        """
        payload = {
            "accountReference": customer['reference'],
            "accountName": customer['name'],
            "customerEmail": customer['email'],
            "customerName": customer['name'],
            "contractCode": self.contract_code,
            "currencyCode": "NGN",
            "getAllAvailableBanks": True
}

        response = requests.post(
            f"{self.base_url}/bank-transfer/reserved-accounts",
            json=payload,
            headers=self._get_headers()
)
        response.raise_for_status()
        return response.json()['responseBody']

    def get_reserved_account_details(self, account_reference):
        """
        Fetch details of a reserved account by reference.

:param account_reference: str
:return: dict with account details
        """
        response = requests.get(
            f"{self.base_url}/bank-transfer/reserved-accounts/{account_reference}",
            headers=self._get_headers()
)
        response.raise_for_status()
        return response.json()['responseBody']

    def validate_transaction(self, transaction_reference):
        """
        Validate a transaction using its reference.

:param transaction_reference: str
:return: dict with transaction details
        """
        response = requests.get(
            f"{self.base_url}/transactions/{transaction_reference}",
            headers=self._get_headers()
)
        response.raise_for_status()
        return response.json()['responseBody']

    def initiate_disbursement(self, disbursement):
        """
        Initiate a disbursement (withdrawal) to a bank account.

:param disbursement: dict with keys 'amount', 'reference', 'narration', 'bankCode', 'accountNumber', 'walletId'
:return: dict with disbursement response
        """
        response = requests.post(
            f"{self.base_url}/disbursements/single",
            json=disbursement,
            headers=self._get_headers()
)
        response.raise_for_status()
        return response.json()['responseBody']

    def check_disbursement_status(self, reference):
        """
        Check the status of a disbursement.

:param reference: str
:return: dict with disbursement status
        """
        response = requests.get(
            f"{self.base_url}/disbursements/single/{reference}",
            headers=self._get_headers()
)
        response.raise_for_status()
        return response.json()['responseBody']


    def verify_webhook_signature(transaction_reference, payment_reference, amount_paid, paid_on, transaction_hash, secret_key):
    """
    Verify Monnify webhook signature.

:param transaction_reference: str
:param payment_reference: str
:param amount_paid: str or float
:param paid_on: str (ISO timestamp)
:param transaction_hash: str (from webhook)
:param secret_key: str (your Monnify secret key)
:return: bool
    """
    raw_string = f"{transaction_reference}|{payment_reference}|{amount_paid}|{paid_on}|{secret_key}"
    computed_hash = hashlib.sha512(raw_string.encode()).hexdigest()
    return computed_hash == transaction_hash

    def create_invoice(self, invoice):
    """
    Create a payment invoice.

:param invoice: dict with keys 'amount', 'customerName', 'customerEmail', 'paymentReference', 'description', 'redirectUrl'
:return: dict with invoice details
    """
    payload = {
        "amount": invoice['amount'],
        "customerName": invoice['customerName'],
        "customerEmail": invoice['customerEmail'],
        "paymentReference": invoice['paymentReference'],
        "paymentDescription": invoice['description'],
        "currencyCode": "NGN",
        "contractCode": self.contract_code,
        "redirectUrl": invoice['redirectUrl']
}

    response = requests.post(
        f"{self.base_url}/merchant-invoices/create",
        json=payload,
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']

  def get_invoice_details(self, payment_reference):
    """
    Retrieve invoice details by payment reference.

:param payment_reference: str
:return: dict with invoice details
    """
    response = requests.get(
        f"{self.base_url}/merchant-invoices/query?paymentReference={payment_reference}",
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']

  def list_transactions(self, page=0, size=10):
    """
    List transactions with pagination.

:param page: int
:param size: int
:return: dict with transaction list
    """
    response = requests.get(
        f"{self.base_url}/transactions/search?page={page}&size={size}",
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']

  def get_transaction_details(self, transaction_reference):
    """
    Get full details of a transaction.

:param transaction_reference: str
:return: dict with transaction info
    """
    response = requests.get(
        f"{self.base_url}/transactions/{transaction_reference}",
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']

  def get_wallet_balance(self, wallet_id="defaultWallet"):
    """
    Get the balance of a Monnify wallet.

:param wallet_id: str (default is 'defaultWallet')
:return: dict with wallet balance
    """
    response = requests.get(
        f"{self.base_url}/disbursements/wallet-balance/{wallet_id}",
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']


    def list_wallet_transactions(self, wallet_id="defaultWallet", page=0, size=10):
    """
    List transactions from a Monnify wallet.

:param wallet_id: str
:param page: int
:param size: int
:return: dict with transaction list
    """
    response = requests.get(
        f"{self.base_url}/disbursements/wallet-transactions/{wallet_id}?page={page}&size={size}",
        headers=self._get_headers()
)
    response.raise_for_status()
    return response.json()['responseBody']

"""
Example usage

from monnify_service import MonnifyService

monnify = MonnifyService(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    contract_code="YOUR_CONTRACT_CODE"
)

# Create a reserved account
account = monnify.create_reserved_account({
    "reference": "user123",
    "name": "Jane Doe",
    "email": "jane@example.com"
})

print("Reserved Account:", account)
"""