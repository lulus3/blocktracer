import streamlit as st

from services.contract_service import get_participant, participant_label, send_transaction, short_address


class AdminPage:
    def render(self):
        st.header("Administração de participantes")
        owner = st.contract.functions.owner().call()
        st.write("**Administrador do contrato:**", participant_label(owner))
        st.write("**Carteira conectada:**", participant_label(st.sender_address))

        if owner.lower() != st.sender_address.lower():
            st.warning("A carteira conectada não é a administradora. Alterações de permissão serão rejeitadas.")

        st.caption("Cadastre a identificação e as permissões das contas locais do Ganache.")
        account = st.selectbox(
            "Carteira do participante",
            options=st.session_state.available_accounts,
            format_func=short_address,
            key="admin_selected_account",
        )
        participant = get_participant(account)

        if participant["exists"]:
            st.info(f"Dados já cadastrados: {participant['name']} · {participant['organization']}")

        with st.form("participant_form"):
            participant_name = st.text_input(
                "Nome do participante",
                value=participant["name"],
                placeholder="Ex.: Maria Santos",
                key=f"participant_name_{account}",
            )
            organization_name = st.text_input(
                "Empresa ou organização",
                value=participant["organization"],
                placeholder="Ex.: Distribuidora Norte",
                key=f"participant_organization_{account}",
            )
            left, right = st.columns(2)
            with left:
                manufacturer_authorized = st.checkbox(
                    "Autorizar como fabricante",
                    value=participant["is_manufacturer"],
                    key=f"participant_manufacturer_{account}",
                )
            with right:
                custodian_authorized = st.checkbox(
                    "Autorizar como custodiante",
                    value=participant["is_custodian"],
                    key=f"participant_custodian_{account}",
                )
            submitted = st.form_submit_button("Salvar participante", use_container_width=True)

        if submitted:
            if not participant_name.strip() or not organization_name.strip():
                st.error("Informe o nome e a organização do participante.")
                return
            function = st.contract.functions.registerParticipant(
                account,
                participant_name.strip(),
                organization_name.strip(),
                manufacturer_authorized,
                custodian_authorized,
            )
            success, message, receipt = send_transaction(function)
            if success:
                st.success(f"Participante {short_address(account)} atualizado no bloco #{receipt.blockNumber}.")
            else:
                st.error(message)
