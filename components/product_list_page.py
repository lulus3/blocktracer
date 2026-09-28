import streamlit as st

from services.product_query import get_registered_products


class ProductListPage:
    PAGE_SIZE = 10

    @staticmethod
    def _matches_search(product, search_term):
        searchable_fields = (
            product["product_id"],
            product["product_name"],
            product["batch_number"],
            product["manufacturer_name"],
            product["manufacturing_location"],
        )
        return any(search_term in value.lower() for value in searchable_fields)

    @staticmethod
    def _show_details(product):
        left, right = st.columns(2)
        with left:
            st.write("**Data de fabricação:**", product["manufacture_date"])
            st.write("**Fabricante:**", product["manufacturer_name"])
            st.write("**Local:**", product["manufacturing_location"])
            st.write("**Status:**", product["status"])
        with right:
            st.write("**Registrado em:**", product["registered_at"])
            st.write("**Carteira do fabricante:**", product["manufacturer_account"])
            st.write("**Custodiante atual:**", product["current_custodian"])
            st.write("**Descrição:**", product["brief_description"])

    def render(self):
        st.header("Consultar produtos")
        st.caption("Pesquise produtos já registrados na blockchain local.")

        try:
            products = get_registered_products()
        except Exception as error:
            st.error(f"Não foi possível consultar os produtos na blockchain: {error}")
            return

        search_term = st.text_input(
            "Pesquisar por nome, lote, fabricante, local ou ID",
            placeholder="Ex.: carregador, LOTE-2026, Manaus",
        ).strip().lower()

        filtered_products = [
            product for product in products if not search_term or self._matches_search(product, search_term)
        ]

        st.metric("Produtos encontrados", len(filtered_products))

        if not filtered_products:
            st.info("Nenhum produto encontrado. Registre um produto ou altere a busca.")
            return

        total_pages = (len(filtered_products) - 1) // self.PAGE_SIZE + 1
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
        start = (page - 1) * self.PAGE_SIZE
        products_page = filtered_products[start : start + self.PAGE_SIZE]

        table_rows = [
            {
                "Produto": product["product_name"],
                "Lote": product["batch_number"],
                "Fabricante": product["manufacturer_name"],
                "Status": product["status"],
                "ID": product["product_id"],
            }
            for product in products_page
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        st.caption(f"Exibindo {start + 1}-{start + len(products_page)} de {len(filtered_products)} produto(s).")
        for product in products_page:
            label = f"{product['product_name']} — lote {product['batch_number']}"
            with st.expander(label):
                self._show_details(product)
                st.code(product["product_id"], language=None)
