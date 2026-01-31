# text_engine.py
# Interpretação determinística on-chain (fase 2)

def interpret_exchange_inflow(ma7, percentil):
    if percentil <= 20:
        return (
            f"O Exchange Inflow (MA7) permanece baixo, em {ma7:,} BTC, "
            "indicando baixa pressão vendedora."
        )

    if percentil <= 60:
        return (
            f"O Exchange Inflow (MA7) encontra-se em nível intermediário, "
            f"em {ma7:,} BTC."
        )

    return (
        f"O Exchange Inflow (MA7) apresenta elevação, em {ma7:,} BTC, "
        "sugerindo possível aumento de pressão vendedora."
    )
