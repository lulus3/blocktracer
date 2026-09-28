import io
from datetime import datetime

from PIL import Image
import streamlit as st

from services.contract_service import participant_label, send_transaction, short_address
from services.product_query import get_product, read_product_id_from_qr


class VerifyProduct:
    @staticmethod
    def _show_product(product):
        if product["status"] == "RECOLHIDO":
            st.error("Produto recolhido: não comercialize ou utilize este item.")
        else:
            st.success("Autenticidade confirmada na blockchain local.")

        left, right = st.columns(2)
        with left:
            st.metric("Status", product["status"])
            st.write("**Produto:**", product["product_name"])
            st.write("**Lote:**", product["batch_number"])
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

    @staticmethod
    def _show_history(product_id):
        st.subheader("Histórico de rastreabilidade")
        count = st.contract.functions.getCustodyHistoryCount(product_id).call()

        if count == 0:
            st.info("Nenhuma movimentação encontrada.")
            return

        for index in range(count):
            source, destination, location, timestamp = st.contract.functions.getCustodyRecord(product_id, index).call()
            title = "Origem registrada" if index == 0 else f"Transferência #{index}"
            with st.expander(title, expanded=index == 0):
                st.write("**De:**", "Origem" if int(source, 16) == 0 else short_address(source))
                st.write("**Para:**", participant_label(destination))
                st.write("**Local:**", location)
                st.write("**Data/hora:**", datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S"))

    @staticmethod
    def _render_management_actions(product):
        st.divider()
        st.subheader("Ações de custódia")
        st.caption("O contrato aceitará a transferência apenas da carteira que é o custodiante atual.")

        with st.form("transfer_custody_from_auth"):
            destination_account = st.text_input("Carteira do novo custodiante")
            destination_location = st.text_input("Local de destino")
            transfer = st.form_submit_button("Registrar transferência")

        if transfer:
            if not destination_account or not destination_location:
                st.error("Informe a carteira de destino e o local.")
            else:
                success, message, receipt = send_transaction(
                    st.contract.functions.transferCustody(
                        product["product_id"], destination_account, destination_location
                    )
                )
                if success:
                    st.success(f"Custódia transferida no bloco #{receipt.blockNumber}.")
                    st.rerun()
                else:
                    st.error(message)

        if product["status"] == "ATIVO":
            if st.button("Marcar produto como recolhido", type="secondary"):
                success, message, receipt = send_transaction(
                    st.contract.functions.recallProduct(product["product_id"])
                )
                if success:
                    st.warning(f"Produto recolhido no bloco #{receipt.blockNumber}.")
                    st.rerun()
                else:
                    st.error(message)

    def render(self):
        st.header("Autenticar e rastrear produto")
        st.caption("Informe o ID ou envie o QR Code para confirmar a autenticidade e consultar a trajetória do lote.")

        with st.form("auth_form"):
            product_id = st.text_input("ID do produto")
            uploaded_file = st.file_uploader("QR Code do produto", type=["png", "jpg", "jpeg", "bmp"])
            submitted = st.form_submit_button("Verificar autenticidade", use_container_width=True)

        if submitted:
            try:
                if uploaded_file is not None:
                    image = Image.open(io.BytesIO(uploaded_file.getvalue()))
                    product_id = read_product_id_from_qr(image)

                if not product_id.strip():
                    st.error("Informe um ID ou envie um QR Code.")
                    return

                st.session_state.authenticated_product_id = product_id.strip()
            except Exception as error:
                st.error(f"Não foi possível ler o QR Code: {error}")
                return

        product_id = st.session_state.get("authenticated_product_id")
        if not product_id:
            return

        try:
            product = get_product(product_id)
            if product is None:
                st.error("Produto não encontrado na blockchain.")
                return

            self._show_product(product)
            self._show_history(product_id)
            self._render_management_actions(product)
        except Exception as error:
            st.error(f"Não foi possível consultar o produto: {error}")
