import streamlit as st
from datetime import datetime


class ProductsHistory:
    def __init__(self):
        pass

    def render(self):
        st.header("Estado da Blockchain")
    
        # Exibir status da blockchain
        is_valid = st.session_state.blockchain.is_blockchain_valid()
        if is_valid:
            st.success("✅ Blockchain válida")
        else:
            st.error("❌ Blockchain inválida")
        
        # Exibir blocos
        st.subheader("Blocos da Blockchain")
        
        # Criar um container com altura fixa e scroll
        blockchain_container = st.container()
        
        with blockchain_container:
            for block in st.session_state.blockchain.blocks:
                if block.index != 0:
                    with st.expander(f"Bloco #{block.index}", expanded=True):
                        st.markdown(f"""
                        **Hash Anterior:** `{block.previous_hash}`  
                        **Timestamp:** {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}  
                        **Hash:** `{block.hash}`  
                        **Dados:**
                        **Nome do Produto:** `{block.data.product_name}`  
                        **Número do Lote:** `{block.data.batch_number}`  
                        **Data de Fabricação:** `{block.data.manufacture_date}`  
                        **Fabricante:** `{block.data.manufacturer}`  
                        **Local de Fabricação:** `{block.data.manufacturing_location}`  
                        **Descrição:** `{block.data.brief_description}`
                        **Data de Registro:** `{block.data.capture_date}`
                        **Nonce:** `{block.nonce}`
                        """)
                        st.markdown("---")
                else: 
                    with st.expander(f"Bloco #{block.index}", expanded=True):
                        st.markdown(f"""
                        **Hash Anterior:** `{block.previous_hash}`  
                        **Timestamp:** {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}  
                        **Hash:** `{block.hash}`  
                        **Dados:** `{block.data}`
                        **Nonce:** `{block.nonce}`
                        """)
                        st.markdown("---")
                    
