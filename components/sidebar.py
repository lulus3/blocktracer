import streamlit as st


class Sidebar:
    def render(self):
        st.header("Sobre o sistema")
        st.markdown(
            """
O **BlockTracer** registra a origem e a movimentação de produtos eletrônicos na blockchain local.

**Perfis**

- Administrador: autoriza fabricantes e custodiantes.
- Fabricante autorizado: registra produtos.
- Custodiante autorizado: recebe e transfere produtos.
- Consumidor: pesquisa produtos, consulta o QR Code e vê o histórico.

**Regras aplicadas pelo contrato**

- não aceita ID de produto duplicado;
- bloqueia registro por fabricante não autorizado;
- só o custodiante atual pode transferir o item;
- não permite transferir produto recolhido.
            """
        )
