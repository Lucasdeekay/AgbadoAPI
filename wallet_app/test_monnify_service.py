import hashlib
import unittest
from unittest.mock import MagicMock, patch
from wallet_app.monnify_service import MonnifyService


class TestMonnifyService(unittest.TestCase):
    def setUp(self):
        self.service = MonnifyService(
            api_key="test_api_key",
            secret_key="test_secret_key",
            contract_code="test_contract_code",
            base_url="https://api.monnify.com/api/v1"
)

    @patch("monnify_service.requests.post")
    def test_authenticate(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"accessToken": "mock_token"}
}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        token = self.service.authenticate()
        self.assertEqual(token, "mock_token")

    @patch("monnify_service.requests.post")
    def test_create_reserved_account(self, mock_post):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"accountNumber": "1234567890"}
}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        customer = {
            "reference": "user123",
            "name": "Jane Doe",
            "email": "jane@example.com"
}
        result = self.service.create_reserved_account(customer)
        self.assertEqual(result["accountNumber"], "1234567890")

    @patch("monnify_service.requests.post")
    def test_create_invoice(self, mock_post):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"checkoutUrl": "https://checkout.monnify.com/invoice"}
}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        invoice = {
            "amount": 5000,
            "customerName": "Jane Doe",
            "customerEmail": "jane@example.com",
            "paymentReference": "INV-001",
            "description": "Test Invoice",
            "redirectUrl": "https://example.com/redirect"
}
        result = self.service.create_invoice(invoice)
        self.assertIn("checkoutUrl", result)

    @patch("monnify_service.requests.get")
    def test_get_invoice_details(self, mock_get):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"paymentReference": "INV-001"}
}
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        result = self.service.get_invoice_details("INV-001")
        self.assertEqual(result["paymentReference"], "INV-001")

    @patch("monnify_service.requests.post")
    def test_initiate_disbursement(self, mock_post):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"transactionReference": "WD-001"}
}
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        disbursement = {
            "amount": 1000,
            "reference": "WD-001",
            "narration": "Withdrawal",
            "bankCode": "058",
            "accountNumber": "0123456789",
            "walletId": "defaultWallet"
}
        result = self.service.initiate_disbursement(disbursement)
        self.assertEqual(result["transactionReference"], "WD-001")

    def test_verify_webhook_signature(self):
        transaction_reference = "TRX123"
        payment_reference = "PAY123"
        amount_paid = "1000"
        paid_on = "2023-01-01T12:00:00"
        secret_key = "test_secret_key"

        raw = f"{transaction_reference}|{payment_reference}|{amount_paid}|{paid_on}|{secret_key}"
        expected_hash = hashlib.sha512(raw.encode()).hexdigest()

        is_valid = MonnifyService.verify_webhook_signature(
            transaction_reference,
            payment_reference,
            amount_paid,
            paid_on,
            expected_hash,
            secret_key
)
        self.assertTrue(is_valid)

    @patch("monnify_service.requests.get")
    def test_get_wallet_balance(self, mock_get):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"availableBalance": 50000}
    }
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        result = self.service.get_wallet_balance()
        self.assertEqual(result["availableBalance"], 50000)

    @patch("monnify_service.requests.get")
    def test_list_wallet_transactions(self, mock_get):
        self.service.access_token = "mock_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "responseBody": {"content": [{"reference": "TX001"}]}
    }
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        result = self.service.list_wallet_transactions()
        self.assertEqual(result["content"][0]["reference"], "TX001")

    def test_get_supported_banks(self):
        banks = self.service.get_supported_banks()
        self.assertTrue(any(bank["code"] == "058" for bank in banks))  # GTB
        self.assertEqual(len(banks), 4)

if name == "main":
    unittest.main()