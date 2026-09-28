from datetime import date
import io
import json
import uuid

import qrcode
import streamlit as st

from services.contract_service import send_transaction


class RegisterProduct:
    @staticmethod
    def _qrcode(product_id):
        payload = json.dumps({"product_id": product_id})
        image = qrcode.make(payload)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def render(self):
        st.header("Registrar novo produto")
        st.caption("Somente uma carteira autorizada como fabricante pode gravar um produto.")

        with st.form("product_form", clear_on_submit=True):
            left, right = st.columns(2)
            with left:
                product_name = st.text_input("Nome do produto")
                batch_number = st.text_input("Número do lote")
                manufacture_date = st.date_input(
                    "Data de fabricação", value=date.today(), max_value=date.today(), format="DD/MM/YYYY"
                )
            with right:
                manufacturer_name = st.text_input("Fabricante")
                manufacturing_location = st.text_input("Local de fabricação")
                brief_description = st.text_area("Descrição breve")

            submitted = st.form_submit_button("Registrar produto", use_container_width=True)

        if not submitted:
            return

        values = [product_name, batch_number, manufacturer_name, manufacturing_location, brief_description]
        if not all(value.strip() for value in values):
            st.error("Preencha todos os campos obrigatórios.")
            return

        product_id = uuid.uuid4().hex
        result, message, receipt = send_transaction(
            st.contract.functions.register(
                product_id,
                product_name.strip(),
                batch_number.strip(),
                manufacture_date.isoformat(),
                manufacturer_name.strip(),
                manufacturing_location.strip(),
                brief_description.strip(),
            )
        )

        if not result:
            st.error(message)
            return

        qr_code = self._qrcode(product_id)
        st.success("Produto registrado e confirmado na blockchain local.")
        st.code(product_id, language=None)
        st.caption(
            f"Bloco #{receipt.blockNumber} · transação `{receipt.transactionHash.hex()}`"
        )
        st.image(qr_code, width=260, caption="QR Code de consulta do produto")
        st.download_button(
            "Baixar QR Code",
            data=qr_code,
            file_name=f"produto-{product_id}.png",
            mime="image/png",
        )
