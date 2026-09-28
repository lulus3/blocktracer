import streamlit as st


def send_transaction(contract_function):
    """Envia uma transação pela conta desbloqueada do Ganache selecionada na sessão."""
    try:
        nonce = st.w3.eth.get_transaction_count(st.sender_address, "pending")
        transaction = contract_function.build_transaction(
            {
                "from": st.sender_address,
                "nonce": nonce,
                "gasPrice": st.w3.eth.gas_price,
            }
        )
        estimated_gas = st.w3.eth.estimate_gas(transaction)
        transaction["gas"] = int(estimated_gas * 1.2)

        transaction_hash = st.w3.eth.send_transaction(transaction)
        receipt = st.w3.eth.wait_for_transaction_receipt(transaction_hash)

        if receipt.status != 1:
            return False, "A transação foi rejeitada pelo contrato.", None

        return True, "Transação confirmada.", receipt
    except Exception as error:
        return False, f"Transação rejeitada: {error}", None


def short_address(address):
    if not address:
        return "—"
    return f"{address[:6]}...{address[-4:]}"


def get_participant(account):
    exists, name, organization, is_manufacturer, is_custodian = st.contract.functions.getParticipant(account).call()
    return {
        "exists": exists,
        "name": name,
        "organization": organization,
        "is_manufacturer": is_manufacturer,
        "is_custodian": is_custodian,
    }


def participant_label(account):
    participant = get_participant(account)
    if not participant["exists"]:
        return short_address(account)
    return f"{participant['name']} · {participant['organization']} ({short_address(account)})"
