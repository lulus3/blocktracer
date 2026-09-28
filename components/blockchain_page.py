from datetime import datetime

import streamlit as st

from services.contract_service import participant_label, short_address


class BlockchainPage:
    def render(self):
        st.header("Blockchain local")
        latest_block = st.w3.eth.block_number
        first, second, third = st.columns(3)
        first.metric("Chain ID", st.w3.eth.chain_id)
        second.metric("Último bloco", latest_block)
        third.metric("Conta conectada", short_address(st.sender_address))
        st.caption(f"Participante ativo: {participant_label(st.sender_address)}")
        st.caption(f"Contrato: {st.contract.address}")

        st.subheader("Blocos recentes")
        start = max(0, latest_block - 9)
        for number in range(latest_block, start - 1, -1):
            block = st.w3.eth.get_block(number, full_transactions=True)
            timestamp = datetime.fromtimestamp(block.timestamp).strftime("%d/%m/%Y %H:%M:%S")
            with st.expander(f"Bloco #{number} · {len(block.transactions)} transação(ões)", expanded=number == latest_block):
                st.write("**Hash:**", block.hash.hex())
                st.write("**Data/hora:**", timestamp)
                st.write("**Minerador:**", short_address(block.miner))
                for transaction in block.transactions:
                    st.code(
                        f"Hash: {transaction.hash.hex()}\n"
                        f"De: {transaction['from']}\n"
                        f"Para: {transaction['to']}\n"
                        f"Gas: {transaction['gas']}",
                        language=None,
                    )
