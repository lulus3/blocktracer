import streamlit as st

from services.contract_service import get_participant, short_address


class WalletSelector:
    @staticmethod
    def _get_profile(account, owner):
        participant = get_participant(account)
        roles = []
        if account.lower() == owner.lower():
            roles.append("Administrador")
        if participant["is_manufacturer"]:
            roles.append("Fabricante")
        if participant["is_custodian"]:
            roles.append("Custodiante")
        return " · ".join(roles) if roles else "Consultor (sem permissão de escrita)"

    def render(self):
        owner = st.contract.functions.owner().call()
        accounts = st.session_state.available_accounts
        profiles = {account: self._get_profile(account, owner) for account in accounts}
        participants = {account: get_participant(account) for account in accounts}

        if st.session_state.get("active_wallet") not in accounts:
            st.session_state.active_wallet = accounts[0]

        with st.sidebar:
            st.divider()
            st.subheader("Carteira ativa")
            selected_account = st.selectbox(
                "Conta Ganache",
                options=accounts,
                key="active_wallet",
                format_func=lambda account: (
                    f"{participants[account]['name']} — {participants[account]['organization']}"
                    if participants[account]["exists"]
                    else f"{short_address(account)} — {profiles[account]}"
                ),
            )
            st.caption(f"Endereço: `{selected_account}`")
            st.info(profiles[selected_account])
            st.caption("Modo local: o Ganache assina somente para contas de teste desbloqueadas.")

        st.sender_address = selected_account
        st.active_profile = profiles[selected_account]
