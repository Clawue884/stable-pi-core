import json
import os
from datetime import datetime
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


class Wallet:
    def __init__(self):
        self.private_key = self.generate_private_key()
        self.public_key = self.private_key.public_key()
        self.balances = {}
        self.transaction_history = []

    def generate_private_key(self):
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

    def export_private_key(self, password=None):
        encryption_algorithm = serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=encryption_algorithm
        )

    def export_public_key(self):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def get_balance(self, currency):
        return self.balances.get(currency, 0)

    def sync_balance(self, blockchain_api_url, address):
        """
        Mengambil saldo dari blockchain tertentu menggunakan API publik.
        """
        try:
            response = requests.get(f"{blockchain_api_url}/address/{address}/balance")
            response.raise_for_status()
            data = response.json()
            self.balances.update(data)
        except Exception as e:
            print(f"Error syncing balance: {e}")

    def transfer(self, to_address, currency, amount, blockchain_api_url, private_key=None):
        """
        Transfer ke dompet lain melalui blockchain tertentu.
        """
        if self.get_balance(currency) < amount:
            raise ValueError("Insufficient balance.")

        try:
            transaction = {
                "from": self.export_public_key().decode(),
                "to": to_address,
                "currency": currency,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }

            # Mengirim transaksi ke blockchain melalui API
            response = requests.post(f"{blockchain_api_url}/transactions", json=transaction)
            response.raise_for_status()

            # Update balance lokal
            self.balances[currency] -= amount

            # Catat transaksi
            self.record_transaction(to_address, currency, amount)

        except Exception as e:
            print(f"Error in transaction: {e}")

    def record_transaction(self, to_address, currency, amount):
        transaction = {
            "timestamp": datetime.now().isoformat(),
            "to": to_address,
            "currency": currency,
            "amount": amount
        }
        self.transaction_history.append(transaction)

    def get_transaction_history(self):
        return self.transaction_history


if __name__ == "__main__":
    # Inisialisasi wallet
    wallet1 = Wallet()
    wallet2 = Wallet()

    # Sync balance dari blockchain API
    blockchain_api_url = "https://mock-blockchain-api.com"
    wallet1.sync_balance(blockchain_api_url, "wallet1-address")
    wallet2.sync_balance(blockchain_api_url, "wallet2-address")

    # Menampilkan saldo awal
    print("Wallet 1 Balance:", wallet1.balances)
    print("Wallet 2 Balance:", wallet2.balances)

    # Melakukan transfer
    wallet1.transfer(
        to_address="wallet2-address",
        currency="ETH",
        amount=1.0,
        blockchain_api_url=blockchain_api_url
    )

    # Menampilkan saldo setelah transfer
    print("Wallet 1 Balance after transfer:", wallet1.balances)
    print("Wallet 2 Balance after transfer:", wallet2.balances)

    # Menampilkan riwayat transaksi
    print("Transaction History:", json.dumps(wallet1.get_transaction_history(), indent=4))
