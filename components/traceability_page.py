from datetime import datetime

import streamlit as st

from services.contract_service import send_transaction, short_address
from services.product_query import get_product


class TraceabilityPage:
    @staticmethod
    def _show_history(product_id):
        count = st.contract.functions.getCustodyHistoryCount(product_id).call()
        if count == 0:
            st.info("Nenhuma movimentação encontrada.")
            return

        for index in range(count):
            source, destination, location, timestamp = st.contract.functions.getCustodyRecord(product_id, index).call()
            if index == 0:
                title = "Origem registrada"
            else:
                title = f"Transferência #{index}"
            with st.expander(title, expanded=True):
                st.write("**De:**", "Origem" if int(source, 16) == 0 else short_address(source))
                st.write("**Para:**", short_address(destination))
                st.write("**Local:**", location)
                st.write("**Data/hora:**", datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S"))

    def render(self):
        st.header("Rastreabilidade e custódia")
        st.caption("Consulte o histórico de origem ou registre uma transferência para outro participante autorizado.")

        with st.form("trace_lookup"):
            product_id = st.text_input("ID do produto para rastrear", value=st.session_state.get("trace_product_id", ""))
            lookup = st.form_submit_button("Consultar histórico", use_container_width=True)

        if lookup:
            st.session_state.trace_product_id = product_id.strip()

        product_id = st.session_state.get("trace_product_id", "")
        if not product_id:
            return

        try:
            product = get_product(product_id)
            if product is None:
                st.error("Produto não encontrado.")
                return

            st.write(f"### {product['product_name']} · {product['status']}")
            self._show_history(product_id)
        except Exception as error:
            st.error(f"Não foi possível consultar o histórico: {error}")
            return

        st.divider()
        st.subheader("Transferir custódia")
        with st.form("transfer_custody"):
            destination_account = st.text_input("Carteira do novo custodiante")
            destination_location = st.text_input("Local de destino")
            transfer = st.form_submit_button("Registrar transferência")

        if transfer:
            if not destination_account or not destination_location:
                st.error("Informe a carteira de destino e o local.")
            else:
                success, message, receipt = send_transaction(
                    st.contract.functions.transferCustody(product_id, destination_account, destination_location)
                )
                if success:
                    st.success(f"Custódia transferida no bloco #{receipt.blockNumber}.")
                else:
                    st.error(message)

        if product["status"] == "ATIVO":
            if st.button("Marcar produto como recolhido", type="secondary"):
                success, message, receipt = send_transaction(st.contract.functions.recallProduct(product_id))
                if success:
                    st.warning(f"Produto recolhido no bloco #{receipt.blockNumber}.")
                else:
                    st.error(message)
