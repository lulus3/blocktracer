import io
import os
from datetime import datetime

from dotenv import load_dotenv
from PIL import Image
import streamlit as st
from web3 import Web3

from contract_abi import CONTRACT_ABI
from services.contract_service import participant_label, short_address
from services.product_query import get_product, read_product_id_from_qr

load_dotenv()


def configure_contract():
    provider_url = os.getenv("PROVIDER_URL")
    contract_address = os.getenv("CONTRACT_ADDRESS")

    if not provider_url or not contract_address:
        st.error("O serviço de verificação ainda não possui uma blockchain e um contrato configurados.")
        st.stop()

    configuration_key = f"{provider_url}:{contract_address.lower()}"
    if st.session_state.get("verifier_configuration") != configuration_key:
        web3 = Web3(Web3.HTTPProvider(provider_url))
        if not web3.is_connected():
            st.error("Não foi possível conectar à blockchain local.")
            st.stop()

        try:
            normalized_address = Web3.to_checksum_address(contract_address)
        except ValueError as error:
            st.error(f"Endereço de contrato inválido: {error}")
            st.stop()

        if not web3.eth.get_code(normalized_address):
            st.error("O contrato configurado não foi encontrado na blockchain local.")
            st.stop()

        st.session_state.verifier_web3 = web3
        st.session_state.verifier_contract = web3.eth.contract(address=normalized_address, abi=CONTRACT_ABI)
        st.session_state.verifier_configuration = configuration_key

    # Os serviços de consulta existentes usam estes atributos, sem uma carteira ou chave privada.
    st.w3 = st.session_state.verifier_web3
    st.contract = st.session_state.verifier_contract


def show_product(product):
    if product["status"] == "RECOLHIDO":
        st.error("Produto recolhido: não comercialize ou utilize este item.")
    else:
        st.success("Autenticidade confirmada na blockchain local.")

    left, right = st.columns(2)
    with left:
        st.write("**Produto:**", product["product_name"])
        st.write("**Lote:**", product["batch_number"])
        st.write("**Status:**", product["status"])
        st.write("**Fabricado em:**", product["manufacture_date"])
        st.write("**Fabricante:**", product["manufacturer_name"])
    with right:
        st.write("**Local de fabricação:**", product["manufacturing_location"])
        st.write("**Descrição:**", product["brief_description"])
        st.write("**Registro on-chain:**", product["registered_at"])
        st.write("**Fabricante responsável:**", participant_label(product["manufacturer_account"]))
        st.write("**Custodiante atual:**", participant_label(product["current_custodian"]))

    st.caption("ID do produto")
    st.code(product["product_id"], language=None)


def show_history(product_id):
    st.subheader("Histórico de rastreabilidade")
    count = st.contract.functions.getCustodyHistoryCount(product_id).call()

    if count == 0:
        st.info("Nenhuma movimentação encontrada.")
        return

    for index in range(count):
        source, destination, location, timestamp = st.contract.functions.getCustodyRecord(product_id, index).call()
        title = "Origem registrada" if index == 0 else f"Transferência #{index}"
        with st.expander(title, expanded=index == 0):
            st.write("**De:**", "Origem" if int(source, 16) == 0 else participant_label(source))
            st.write("**Para:**", participant_label(destination))
            st.write("**Local:**", location)
            st.write("**Data/hora:**", datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S"))


def main():
    st.set_page_config(page_title="BlockTracer — Verificar produto", page_icon="📷", layout="centered")
    configure_contract()

    st.title("BlockTracer")
    st.subheader("Verificar autenticidade")
    st.caption("Fotografe o QR Code do produto ou informe o ID do lote.")

    camera_image = st.camera_input("Câmera do celular")
    uploaded_image = st.file_uploader("Ou envie uma imagem do QR Code", type=["png", "jpg", "jpeg", "bmp"])
    product_id = st.text_input("ID do produto")

    if st.button("Verificar produto", type="primary", use_container_width=True):
        try:
            image_file = camera_image or uploaded_image
            if image_file is not None:
                image = Image.open(io.BytesIO(image_file.getvalue()))
                product_id = read_product_id_from_qr(image)

            if not product_id.strip():
                st.error("Fotografe/envie um QR Code ou informe o ID do produto.")
            else:
                st.session_state.verifier_product_id = product_id.strip()
        except Exception as error:
            st.error(f"Não foi possível ler o QR Code: {error}")

    selected_product_id = st.session_state.get("verifier_product_id")
    if not selected_product_id:
        return

    try:
        product = get_product(selected_product_id)
        if product is None:
            st.error("Produto não encontrado na blockchain.")
            return

        show_product(product)
        show_history(selected_product_id)
    except Exception as error:
        st.error(f"Não foi possível consultar o produto: {error}")


if __name__ == "__main__":
    main()
