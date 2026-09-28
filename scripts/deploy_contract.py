import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv, set_key
from web3 import Web3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIRECTORY = Path(os.getenv("CONTRACT_ARTIFACT_PATH", PROJECT_ROOT / "artifacts" / "solc"))
ENV_FILE_PATH = Path(os.getenv("ENV_FILE_PATH", PROJECT_ROOT / ".env"))
ABI_PATH = ARTIFACT_DIRECTORY / "ProductsOriginChain.abi"
BYTECODE_PATH = ARTIFACT_DIRECTORY / "ProductsOriginChain.bin"


def main():
    parser = argparse.ArgumentParser(description="Publica o contrato compilado no Ganache.")
    parser.add_argument(
        "--update-env",
        action="store_true",
        help="Atualiza CONTRACT_ADDRESS no .env após um deploy confirmado.",
    )
    arguments = parser.parse_args()

    load_dotenv(ENV_FILE_PATH)
    provider_url = os.getenv("PROVIDER_URL")
    private_key = os.getenv("PRIVATE_KEY")
    if not provider_url or not private_key:
        raise RuntimeError("Defina PROVIDER_URL e PRIVATE_KEY no .env antes do deploy.")
    if not ABI_PATH.exists() or not BYTECODE_PATH.exists():
        raise RuntimeError("Artefatos não encontrados. Execute scripts/compile-contract.ps1 primeiro.")

    web3 = Web3(Web3.HTTPProvider(provider_url))
    if not web3.is_connected():
        raise RuntimeError(f"Não foi possível conectar ao Ganache em {provider_url}.")

    account = web3.eth.account.from_key(private_key)
    abi = json.loads(ABI_PATH.read_text(encoding="utf-8"))
    bytecode = BYTECODE_PATH.read_text(encoding="utf-8").strip()
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)

    transaction = contract.constructor().build_transaction(
        {
            "from": account.address,
            "chainId": web3.eth.chain_id,
            "nonce": web3.eth.get_transaction_count(account.address, "pending"),
            "gasPrice": web3.eth.gas_price,
        }
    )
    transaction["gas"] = int(web3.eth.estimate_gas(transaction) * 1.2)
    signed = web3.eth.account.sign_transaction(transaction, private_key)
    receipt = web3.eth.wait_for_transaction_receipt(web3.eth.send_raw_transaction(signed.raw_transaction))

    if receipt.status != 1 or not receipt.contractAddress:
        raise RuntimeError("O deploy foi rejeitado pela blockchain local.")

    print("Deploy confirmado.")
    print(f"Bloco: {receipt.blockNumber}")
    print(f"Transação: {receipt.transactionHash.hex()}")
    print(f"CONTRACT_ADDRESS={receipt.contractAddress}")

    if arguments.update_env:
        set_key(ENV_FILE_PATH, "CONTRACT_ADDRESS", receipt.contractAddress)
        print("Arquivo .env atualizado com o novo endereço do contrato.")


if __name__ == "__main__":
    main()
