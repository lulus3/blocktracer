import os

from dotenv import load_dotenv
import streamlit as st
from web3 import Web3

from components.admin_page import AdminPage
from components.blockchain_page import BlockchainPage
from components.product_list_page import ProductListPage
from components.register_product import RegisterProduct
from components.verify_product import VerifyProduct
from components.sidebar import Sidebar
from components.wallet_selector import WalletSelector
from contract_abi import CONTRACT_ABI

load_dotenv()


class App:
    @staticmethod
    def _configure_contract():
        provider_url = os.getenv("PROVIDER_URL")
        contract_address = os.getenv("CONTRACT_ADDRESS")

        if not all([provider_url, contract_address]):
            st.error("Preencha PROVIDER_URL e CONTRACT_ADDRESS no arquivo .env.")
            st.stop()

        configuration_key = f"{provider_url}:{contract_address.lower()}"
        try:
            normalized_contract_address = Web3.to_checksum_address(contract_address)
        except ValueError as error:
            st.error(f"Configuração inválida no .env: {error}")
            st.stop()

        if st.session_state.get("contract_configuration") != configuration_key:
            web3 = Web3(Web3.HTTPProvider(provider_url))
            if not web3.is_connected():
                st.error(f"Não foi possível conectar à blockchain em {provider_url}.")
                st.stop()

            if not web3.eth.get_code(normalized_contract_address):
                st.error("O CONTRACT_ADDRESS não possui um contrato publicado nesta rede.")
                st.stop()

            accounts = [Web3.to_checksum_address(account) for account in web3.eth.accounts]
            if not accounts:
                st.error("A rede não disponibilizou contas desbloqueadas para o modo local.")
                st.stop()

            st.session_state.web3 = web3
            st.session_state.contract = web3.eth.contract(address=normalized_contract_address, abi=CONTRACT_ABI)
            st.session_state.available_accounts = accounts
            st.session_state.contract_configuration = configuration_key
            st.session_state.active_wallet = accounts[0]

        st.w3 = st.session_state.web3
        st.contract = st.session_state.contract

    @staticmethod
    def run():
        st.set_page_config(page_title="BlockTracer", page_icon="🔗", layout="wide")
        App._configure_contract()
        WalletSelector().render()

        st.title("BlockTracer")
        st.caption("Rastreabilidade e autenticação de produtos em blockchain local")

        pages = {
            "Registrar": RegisterProduct(),
            "Consultar produtos": ProductListPage(),
            "Autenticar e rastrear": VerifyProduct(),
            "Blockchain": BlockchainPage(),
        }
        owner = st.contract.functions.owner().call()
        if st.sender_address.lower() == owner.lower():
            pages["Administração"] = AdminPage()
        selected_page = st.radio(
            "Navegação",
            list(pages),
            horizontal=True,
            label_visibility="collapsed",
            key="selected_page",
        )
        pages[selected_page].render()

        with st.sidebar:
            Sidebar().render()


App.run()
