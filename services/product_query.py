from datetime import datetime
import json

from pyzbar.pyzbar import decode
import streamlit as st


def read_product_id_from_qr(image):
    decoded = decode(image)
    if not decoded:
        raise ValueError("Não foi possível ler um QR Code nesta imagem.")

    payload = json.loads(decoded[0].data.decode("utf-8"))
    product_id = payload.get("product_id")
    if not product_id:
        raise ValueError("O QR Code não pertence ao BlockTracer.")
    return product_id


def get_product(product_id):
    values = st.contract.functions.getProductSummary(product_id).call()
    (
        exists,
        stored_product_id,
        product_name,
        batch_number,
        registered_at,
        status,
    ) = values

    if not exists:
        return None

    (
        manufacture_date,
        manufacturer_name,
        manufacturing_location,
        brief_description,
        manufacturer_account,
        current_custodian,
    ) = st.contract.functions.getProductDetails(product_id).call()

    return {
        "product_id": stored_product_id,
        "product_name": product_name,
        "batch_number": batch_number,
        "manufacture_date": manufacture_date,
        "manufacturer_name": manufacturer_name,
        "manufacturing_location": manufacturing_location,
        "brief_description": brief_description,
        "manufacturer_account": manufacturer_account,
        "current_custodian": current_custodian,
        "registered_at": datetime.fromtimestamp(registered_at).strftime("%d/%m/%Y %H:%M:%S"),
        "status": "ATIVO" if status == 0 else "RECOLHIDO",
    }


def get_registered_products():
    """Lê os produtos da blockchain local para a tela de consulta.

    A filtragem é feita na interface, sem gravar uma cópia paralela dos dados.
    """
    total = st.contract.functions.getProductCount().call()
    products = []

    for index in range(total):
        product_id = st.contract.functions.getProductIdAt(index).call()
        product = get_product(product_id)
        if product is not None:
            products.append(product)

    return products
