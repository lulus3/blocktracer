import os
from pathlib import Path
import unittest
import uuid

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError

from contract_abi import CONTRACT_ABI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


class ProductOriginChainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        provider_url = os.getenv("PROVIDER_URL")
        private_key = os.getenv("PRIVATE_KEY")
        contract_address = os.getenv("CONTRACT_ADDRESS")
        if not all([provider_url, private_key, contract_address]):
            raise RuntimeError("Crie o .env com PROVIDER_URL, PRIVATE_KEY e CONTRACT_ADDRESS antes de executar os testes.")

        cls.w3 = Web3(Web3.HTTPProvider(provider_url))
        if not cls.w3.is_connected():
            raise RuntimeError("Não foi possível conectar ao Ganache.")

        cls.private_key = private_key
        cls.sender = cls.w3.eth.account.from_key(private_key).address
        cls.contract = cls.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=CONTRACT_ABI)
        if not cls.contract.functions.authorizedManufacturers(cls.sender).call():
            raise RuntimeError("A carteira do .env não é fabricante autorizada neste contrato.")

    @classmethod
    def _send(cls, function):
        transaction = function.build_transaction(
            {
                "from": cls.sender,
                "chainId": cls.w3.eth.chain_id,
                "nonce": cls.w3.eth.get_transaction_count(cls.sender, "pending"),
                "gasPrice": cls.w3.eth.gas_price,
            }
        )
        transaction["gas"] = int(cls.w3.eth.estimate_gas(transaction) * 1.2)
        signed = cls.w3.eth.account.sign_transaction(transaction, cls.private_key)
        receipt = cls.w3.eth.wait_for_transaction_receipt(cls.w3.eth.send_raw_transaction(signed.raw_transaction))
        return receipt

    def test_unknown_product_returns_false(self):
        product = self.contract.functions.getProductSummary(f"unknown-{uuid.uuid4().hex}").call()
        self.assertFalse(product[0])

    def test_valid_registration_and_duplicate_rejection(self):
        product_id = f"test-{uuid.uuid4().hex}"
        product_count_before = self.contract.functions.getProductCount().call()
        registration = self.contract.functions.register(
            product_id,
            "Produto de teste",
            "LOTE-TESTE",
            "2026-09-28",
            "Fabricante de teste",
            "Manaus",
            "Registro criado por teste automatizado",
        )
        receipt = self._send(registration)
        self.assertEqual(receipt.status, 1)

        product = self.contract.functions.getProductSummary(product_id).call()
        self.assertTrue(product[0])
        self.assertEqual(product[2], "Produto de teste")
        self.assertEqual(product[5], 0)  # Active
        self.assertEqual(self.contract.functions.getProductCount().call(), product_count_before + 1)
        self.assertEqual(self.contract.functions.getProductIdAt(product_count_before).call(), product_id)

        with self.assertRaises((ContractLogicError, ValueError)):
            registration.call({"from": self.sender})

    def test_unauthorized_account_cannot_register(self):
        unauthorized = next(account for account in self.w3.eth.accounts if account.lower() != self.sender.lower())
        with self.assertRaises((ContractLogicError, ValueError)):
            self.contract.functions.register(
                f"unauthorized-{uuid.uuid4().hex}",
                "Produto inválido",
                "LOTE-INVALIDO",
                "2026-09-28",
                "Fabricante inválido",
                "Manaus",
                "Operação sem permissão",
            ).call({"from": unauthorized})

    def test_administrator_can_identify_participant(self):
        participant = next(account for account in self.w3.eth.accounts if account.lower() != self.sender.lower())
        receipt = self._send(
            self.contract.functions.registerParticipant(
                participant,
                "Participante de teste",
                "Organização de teste",
                False,
                True,
            )
        )
        self.assertEqual(receipt.status, 1)
        identity = self.contract.functions.getParticipant(participant).call()
        self.assertEqual(identity[1], "Participante de teste")
        self.assertEqual(identity[2], "Organização de teste")
        self.assertFalse(identity[3])
        self.assertTrue(identity[4])


if __name__ == "__main__":
    unittest.main()
