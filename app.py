# app.py
import numpy as np
import pandas as pd
import streamlit as st
from src.algorithm import solve_intermediary

st.set_page_config(layout="wide", page_title="Zagadnienie Pośrednika – NW")

st.markdown(
    """
<style>
    header.stAppHeader { background-color: transparent; }
    section.stMain .block-container { padding-top: 1rem; }
    .stAppDeployButton { display:none }
    .dataframe { font-size: 14px; }
</style>""",
    unsafe_allow_html=True,
)



def sync_supply_data():
    """Synchronizuje koszty zakupu i macierz transportu z listą dostawców"""
    current_suppliers = st.session_state.supply_df["Dostawca"].tolist()

    current_buy = st.session_state.buy_cost_df
    current_buy_suppliers = current_buy["Dostawca"].tolist()

    if current_buy_suppliers != current_suppliers:
        new_buy = pd.DataFrame({"Dostawca": current_suppliers, "Koszt zakupu": 0})
        for i, supplier in enumerate(current_buy_suppliers):
            if supplier in current_suppliers:
                idx = current_suppliers.index(supplier)
                new_buy.loc[idx, "Koszt zakupu"] = current_buy.iloc[i, 1]
        st.session_state.buy_cost_df = new_buy

    current_transport = st.session_state.transport_df
    current_rows = current_transport.index.tolist()
    current_cols = current_transport.columns.tolist()
    new_cols = st.session_state.demand_df["Odbiorca"].tolist()

    if current_rows != current_suppliers or current_cols != new_cols:
        new_transport = pd.DataFrame(0, index=current_suppliers, columns=new_cols)
        for i, row in enumerate(current_rows):
            if row in current_suppliers:
                for j, col in enumerate(current_cols):
                    if col in new_cols:
                        new_transport.loc[row, col] = current_transport.iloc[i, j]
        st.session_state.transport_df = new_transport

    current_blocked = st.session_state.blocked_df
    current_blocked_rows = current_blocked.index.tolist()

    if current_blocked_rows != current_suppliers or current_cols != new_cols:
        new_blocked = pd.DataFrame(False, index=current_suppliers, columns=new_cols)
        for i, row in enumerate(current_blocked_rows):
            if row in current_suppliers:
                for j, col in enumerate(current_blocked.columns):
                    if col in new_cols:
                        new_blocked.loc[row, col] = current_blocked.iloc[i, j]
        st.session_state.blocked_df = new_blocked


def sync_demand_data():
    """Synchronizuje ceny sprzedaży i macierz transportu z listą odbiorców"""
    current_customers = st.session_state.demand_df["Odbiorca"].tolist()

    current_sell = st.session_state.sell_price_df
    current_sell_customers = current_sell["Odbiorca"].tolist()

    if current_sell_customers != current_customers:
        new_sell = pd.DataFrame({"Odbiorca": current_customers, "Cena sprzedaży": 0})
        for i, customer in enumerate(current_sell_customers):
            if customer in current_customers:
                idx = current_customers.index(customer)
                new_sell.loc[idx, "Cena sprzedaży"] = current_sell.iloc[i, 1]
        st.session_state.sell_price_df = new_sell

    current_transport = st.session_state.transport_df
    current_rows = current_transport.index.tolist()
    current_cols = current_transport.columns.tolist()
    new_rows = st.session_state.supply_df["Dostawca"].tolist()

    if current_rows != new_rows or current_cols != current_customers:
        new_transport = pd.DataFrame(0, index=new_rows, columns=current_customers)
        for i, row in enumerate(current_rows):
            if row in new_rows:
                for j, col in enumerate(current_cols):
                    if col in current_customers:
                        new_transport.loc[row, col] = current_transport.iloc[i, j]
        st.session_state.transport_df = new_transport

    current_blocked = st.session_state.blocked_df
    current_blocked_rows = current_blocked.index.tolist()
    current_blocked_cols = current_blocked.columns.tolist()

    if current_blocked_rows != new_rows or current_blocked_cols != current_customers:
        new_blocked = pd.DataFrame(False, index=new_rows, columns=current_customers)
        for i, row in enumerate(current_blocked_rows):
            if row in new_rows:
                for j, col in enumerate(current_blocked_cols):
                    if col in current_customers:
                        new_blocked.loc[row, col] = current_blocked.iloc[i, j]
        st.session_state.blocked_df = new_blocked

# ============================================================
# POMOCNICZE
# ============================================================


# ============================================================
# INICJALIZACJA DATAFRAME'ÓW W SESSION STATE
# ============================================================

if "supply_df" not in st.session_state:
    st.session_state.supply_df = pd.DataFrame(
        {"Dostawca": ["D1", "D2"], "Podaż": [20, 30]}
    )

if "demand_df" not in st.session_state:
    st.session_state.demand_df = pd.DataFrame(
        {"Odbiorca": ["O1", "O2", "O3"], "Popyt": [10, 28, 27]}
    )

if "buy_cost_df" not in st.session_state:
    st.session_state.buy_cost_df = pd.DataFrame(
        {"Dostawca": ["D1", "D2"], "Koszt zakupu": [10, 12]}
    )

if "sell_price_df" not in st.session_state:
    st.session_state.sell_price_df = pd.DataFrame(
        {"Odbiorca": ["O1", "O2", "O3"], "Cena sprzedaży": [30, 25, 30]}
    )

if "transport_df" not in st.session_state:
    st.session_state.transport_df = pd.DataFrame(
        [[8, 14, 17], [12, 9, 19]], index=["D1", "D2"], columns=["O1", "O2", "O3"]
    )
    st.session_state.transport_df.index.name = "Dostawca\\Odbiorca"

if "blocked_df" not in st.session_state:
    blocked_data = np.full((2, 3), False)
    st.session_state.blocked_df = pd.DataFrame(
        blocked_data, index=["D1", "D2"], columns=["O1", "O2", "O3"]
    )
    st.session_state.blocked_df.index.name = "Dostawca\\Odbiorca"

# ============================================================
# UI
# ============================================================

st.title("Zagadnienie pośrednika")

tabs = st.tabs(
    [
        "Dane dostawców i odbiorców",
        "Blokowanie tras",
        "Rozwiązanie",
        "Opis programu",
    ]
)

with tabs[0]:

    if "should_rerun" not in st.session_state:
        st.session_state.should_rerun = False
    col1, col2 = st.columns(2)

    # KOLUMNA LEWA
    with col1:

        #DOSTAWCY
        st.subheader("Podaż dostawców")
        if "key_supply" not in st.session_state: st.session_state.key_supply = 0
        supply_key = f"supply_editor{st.session_state.key_supply}"
        edited_supply = st.data_editor(
            st.session_state.supply_df,
            column_config={
                "_index": st.column_config.Column("Indeks", disabled=True),
                "Dostawca": st.column_config.TextColumn(required=True, validate=r"^.{1,}$"),
                "Podaż": st.column_config.NumberColumn(format="%.2f", required=True)
            },
            hide_index=True,
            num_rows="dynamic",
            width='stretch',
            key=supply_key,
        )

        supply_not_changed = edited_supply.reset_index(drop=True).equals(st.session_state.supply_df.reset_index(drop=True))
        supply_is_not_unique = not edited_supply["Dostawca"].is_unique

        B1, B2 = st.columns(2)
        with B1:
            if st.button("Zatwierdź dostawców",
                        width='stretch',
                        disabled=supply_not_changed or supply_is_not_unique,
                        type="primary",
                        key="confirm_supply",
                        ):
                st.session_state.supply_df = edited_supply.reset_index(drop=True)
                sync_supply_data()
                st.session_state.should_rerun = True
        with B2:
            if st.button("Anuluj zmiany",
                        width='stretch',
                        disabled=supply_not_changed,
                        type="primary",
                        key="cancel_supply"
                        ):
                st.session_state.key_supply += 1
                st.session_state.should_rerun = True

        if not edited_supply["Dostawca"].is_unique:
            st.error("Zduplikowano nazwy dostawców. Popraw dane, aby móc zatwierdzić.")

        with st.expander("Uwaga dotycząca synchronizacji danych"):
            st.write("""
                Zatwierdzenie zmian w tej tabeli może spowodować automatyczną aktualizację danych w używających ich modułach.
                **Wszystkie niezatwierdzone zmiany w poniższych tabelach mogą przepaść:**
                * Koszty zakupu
                * Koszty transportu
            """)


        #KOSZTA ZAKUPU
        st.subheader("Koszty zakupu")
        if "key_buy" not in st.session_state: st.session_state.key_buy = 0
        buy_key=f"buy_editor{st.session_state.key_buy}"
        edited_buy = st.data_editor(
            st.session_state.buy_cost_df,
            column_config={
                "_index": st.column_config.Column("Indeks", disabled=True),
                "Dostawca": st.column_config.Column(disabled=True),
                "Koszt zakupu": st.column_config.NumberColumn(format="%.2f", required=True)
            },
            hide_index=True,
            num_rows="fixed",
            width='stretch',
            key=buy_key,
        )

        buy_not_changed = edited_buy.reset_index(drop=True).equals(st.session_state.buy_cost_df.reset_index(drop=True))

        B1, B2 = st.columns(2)
        with B1:
            if st.button("Zatwierdź koszty",
                        width='stretch',
                        disabled=buy_not_changed,
                        type="primary",
                        key="confirm_buy"
                        ):
                st.session_state.buy_cost_df = edited_buy.reset_index(drop=True)
                st.session_state.should_rerun = True
        with B2:
            if st.button("Anuluj zmiany",
                        width='stretch',
                        disabled=buy_not_changed,
                        type="primary",
                        key="cancel_buy"
                        ):
                st.session_state.key_buy += 1
                st.session_state.should_rerun = True


    # KOLUMNA PRAWA
    with col2:

        #ODBIORCY
        st.subheader("Popyt odbiorców")
        if "key_demand" not in st.session_state: st.session_state.key_demand = 0
        demand_key=f"demand_editor{st.session_state.key_demand}"
        edited_demand = st.data_editor(
            st.session_state.demand_df,
            column_config={
                "_index": st.column_config.Column("Indeks", disabled=True),
                "Odbiorca": st.column_config.TextColumn(required=True, validate=r"^.{1,}$"),
                "Popyt": st.column_config.NumberColumn(format="%.2f", required=True)
            },
            hide_index=True,
            num_rows="dynamic",
            width='stretch',
            key=demand_key,
        )

        demand_not_changed = edited_demand.reset_index(drop=True).equals(st.session_state.demand_df.reset_index(drop=True))
        demand_is_not_unique = not edited_demand["Odbiorca"].is_unique

        B1, B2 = st.columns(2)
        with B1:
            if st.button("Zatwierdź odbiorców",
                        width='stretch',
                        disabled=demand_not_changed or demand_is_not_unique,
                        type="primary",
                        key="confirm_demand"
                        ):
                st.session_state.demand_df = edited_demand.reset_index(drop=True)
                sync_demand_data()
                st.session_state.should_rerun = True
        with B2:
            if st.button("Anuluj zmiany",
                        width='stretch',
                        disabled=demand_not_changed,
                        type="primary",
                        key="cancel_demand"
                        ):
                st.session_state.key_demand += 1
                st.session_state.should_rerun = True

        if not edited_demand["Odbiorca"].is_unique:
            st.error("Zduplikowano nazwy odbiorców. Popraw dane, aby móc zatwierdzić.")

        with st.expander("Uwaga dotycząca synchronizacji danych"):
            st.write("""
                Zatwierdzenie zmian w tej tabeli może spowodować automatyczną aktualizację danych w używających ich modułach.
                **Wszystkie niezatwierdzone zmiany w poniższych tabelach mogą przepaść:**
                * Ceny sprzedaży
                * Koszty transportu
                * Blokowanie tras
            """)


        #CENY SPRZEDAŻY
        st.subheader("Ceny sprzedaży")
        if "key_sell" not in st.session_state: st.session_state.key_sell = 0
        sell_key=f"sell_editor{st.session_state.key_sell}"
        edited_sell = st.data_editor(
            st.session_state.sell_price_df,
            column_config={
                "_index": st.column_config.Column("Indeks", disabled=True),
                "Odbiorca": st.column_config.Column(disabled=True),
                "Cena sprzedaży": st.column_config.NumberColumn(format="%.2f", required=True)
            },
            hide_index=True,
            num_rows="fixed",
            width='stretch',
            key=sell_key,
        )

        sell_not_changed = edited_sell.reset_index(drop=True).equals(st.session_state.sell_price_df.reset_index(drop=True))

        B1, B2 = st.columns(2)
        with B1:
            if st.button("Zatwierdź ceny",
                        width='stretch',
                        disabled=sell_not_changed,
                        type="primary",
                        key="confirm_sell"
                        ):
                st.session_state.sell_price_df = edited_sell.reset_index(drop=True)
                st.session_state.should_rerun = True
        with B2:
            if st.button("Anuluj zmiany",
                        width='stretch',
                        disabled=sell_not_changed,
                        type="primary",
                        key="cancel_sell"
                        ):
                st.session_state.key_sell += 1
                st.session_state.should_rerun = True


    #KOSZTY TRANSPORTU
    st.subheader("Koszty transportu")
    if "key_transport" not in st.session_state: st.session_state.key_transport = 0
    transport_key=f"transport_editor{st.session_state.key_transport}"

    # Synchronizacja macierzy przed wyświetleniem
    current_suppliers = st.session_state.supply_df["Dostawca"].tolist()
    current_customers = st.session_state.demand_df["Odbiorca"].tolist()

    if (
        st.session_state.transport_df.index.tolist() != current_suppliers
        or st.session_state.transport_df.columns.tolist() != current_customers
    ):
        st.session_state.transport_df = (
            st.session_state.transport_df
            .reindex(index=current_suppliers, columns=current_customers, fill_value=0.0)
        )
        # new_transport = pd.DataFrame(
        #     0, index=current_suppliers, columns=current_customers
        # )
        # old_transport = st.session_state.transport_df
        # for i, row in enumerate(old_transport.index):
        #     if row in current_suppliers:
        #         for j, col in enumerate(old_transport.columns):
        #             if col in current_customers:
        #                 new_transport.loc[row, col] = old_transport.iloc[i, j]
        # st.session_state.transport_df = new_transport

    transport_config = {
        col: st.column_config.NumberColumn(format="%.2f", required=True)
        for col in current_customers
    }
    transport_config["_index"] = st.column_config.Column("Dostawca\\Odbiorca", disabled=True)

    edited_transport = st.data_editor(
        st.session_state.transport_df,
        column_config=transport_config,
        width='stretch',
        key=transport_key,
    )

    transport_not_changed = edited_transport.reset_index(drop=True).equals(st.session_state.transport_df.reset_index(drop=True))

    B1, B2 = st.columns(2)
    with B1:
        if st.button("Zatwierdź koszta transportu",
                    width='stretch',
                    disabled=transport_not_changed,
                    type="primary",
                    key="confirm_transport"
                    ):
            st.session_state.transport_df = edited_transport
            st.session_state.should_rerun = True
    with B2:
        if st.button("Anuluj zmiany",
                    width='stretch',
                    disabled=transport_not_changed,
                    type="primary",
                    key="cancel_transport"
                    ):
            st.session_state.key_transport += 1
            st.session_state.should_rerun = True

    #ODŚWIEŻ (jeśli są zatwierdzone zmiany)
    if st.session_state.should_rerun:
        st.session_state.should_rerun = False
        st.rerun()


#USTAWIANIE BLOKADY NA DANE PARY RZECZYWISTE ODBIORCA-DOSTAWCA
# with tabs[1]:
#     st.subheader("Blokowanie tras")

#     current_suppliers = st.session_state.supply_df["Dostawca"].tolist()
#     current_customers = st.session_state.demand_df["Odbiorca"].tolist()

#     if (
#         st.session_state.blocked_df.index.tolist() != current_suppliers
#         or st.session_state.blocked_df.columns.tolist() != current_customers
#     ):
#         new_blocked = pd.DataFrame(
#             False, index=current_suppliers, columns=current_customers
#         )
#         old_blocked = st.session_state.blocked_df
#         for i, row in enumerate(old_blocked.index):
#             if row in current_suppliers:
#                 for j, col in enumerate(old_blocked.columns):
#                     if col in current_customers:
#                         new_blocked.loc[row, col] = old_blocked.iloc[i, j]
#         st.session_state.blocked_df = new_blocked

#     edited_blocked = st.data_editor(
#         st.session_state.blocked_df, width='stretch', key="blocked_editor"
#     )
#     st.session_state.blocked_df = edited_blocked

#DOBÓR STATUSU NACISKU NA ODBIORCĘ:
#Wymuś - jak na zajęciach, sprowadza się do zablokowania fikcyjnego dostawcy dla tego odbiorcy.
#Normalny priorytet - traktowanie domyślne.
#Wykreśl - całkowicie blokuje jakiekolwiek rzeczywiste dostawy do tego rzeczywistego odbiorcy.
with tabs[1]:
    st.subheader("Blokowanie tras")
    if "key_settings" not in st.session_state: st.session_state.key_settings = 0
    settings_key=f"customer_settings_editor{st.session_state.key_settings}"

    current_customers = st.session_state.demand_df["Odbiorca"].tolist()

    if (
        "customer_settings_df" not in st.session_state
        or st.session_state.customer_settings_df["Odbiorca"].tolist() != current_customers
    ):
        new_settings = pd.DataFrame({
            "Odbiorca": current_customers,
            "Nacisk": "Normalny przydział"
        })

        if "customer_settings_df" in st.session_state:
            old_settings = st.session_state.customer_settings_df
            mapping = dict(zip(old_settings["Odbiorca"], old_settings["Nacisk"]))
            new_settings["Nacisk"] = new_settings["Odbiorca"].map(lambda x: mapping.get(x, "Normalny przydział"))

        st.session_state.customer_settings_df = new_settings

    edited_settings = st.data_editor(
        st.session_state.customer_settings_df,
        column_config={
            "_index": st.column_config.Column("Indeks", disabled=True),
            "Odbiorca": st.column_config.Column(disabled=True),
            "Nacisk": st.column_config.SelectboxColumn(
                "Nacisk",
                options=["Wymuś", "Normalny przydział", "Wykreśl"],
                required=True,
                default="Normalny przydział"
            )
        },
        width='stretch',
        hide_index=True,
        key=settings_key
    )

    settings_not_changed = edited_settings.reset_index(drop=True).equals(st.session_state.customer_settings_df.reset_index(drop=True))
    is_already_reset = (edited_settings["Nacisk"]  == "Normalny przydział").all()

    B1, B2, B3 = st.columns(3)
    with B1:
        if st.button("Zatwierdź blokady",
                    width='stretch',
                    disabled=settings_not_changed,
                    type="primary",
                    key="confirm_settings"
                    ):
            st.session_state.customer_settings_df = edited_settings
            st.rerun()
    with B2:
        if st.button("Resetuj blokady",
                    width='stretch',
                    disabled=is_already_reset,
                    type="primary",
                    key="reset_settings"
                    ):
            st.session_state.customer_settings_df["Nacisk"] = "Normalny przydział"
            st.session_state.key_settings += 1
            st.rerun()
    with B3:
        if st.button("Anuluj zmiany",
                    width='stretch',
                    disabled=settings_not_changed,
                    type="primary",
                    key="cancel_settings"
                    ):
            st.session_state.key_settings += 1
            st.rerun()

    with st.expander("Opis dostępnych nacisków"):
            st.write("""
                * Wymuś - dany odbiorca będzie miał wysoki priorytet - wszelkie dostawy od fikcyjnego dostawcy będą w jego przypadku uznane za skrajnie niekorzystne.
                * Normalny priorytet - dany odbiorca będzie miał normalny priorytet.
                * Wykreśl - rzeczywiści dostawcy będą mieć rzeczywiste zyski z tras do tego odbiorcy traktowane jako skrajnie niekorzystne.
            """)


# rozwiązanie


def prepare_with_fictitious(
    supply, demand, buy_cost, sell_price, transport, supply_names, demand_names, pressure
):
    """Dodaje fikcyjnego dostawcę i fikcyjnego odbiorcę"""
    has_fictional = False
    n_s = len(supply)
    n_d = len(demand)

    total_supply = sum(supply)
    total_demand = sum(demand)

    supply_final = supply.copy()
    demand_final = demand.copy()
    supply_names_final = supply_names.copy()
    demand_names_final = demand_names.copy()

    # Macierz zysku dla rzeczywistych
    z = np.zeros((n_s, n_d))
    for i in range(n_s):
        for j in range(n_d):
            z[i, j] = sell_price[j] - buy_cost[i] - transport[i, j]
            # if blocked[i, j]:
            #     z[i, j] = -1e9

    # Fikcyjny odbiorca
    fictional_demand = max(0, total_supply)
    demand_final.append(fictional_demand)
    demand_names_final.append("OF (Fikcyjny)")
    z = np.hstack([z, np.zeros((n_s, 1))])

    # Fikcyjny dostawca
    fictional_supply = max(0, total_demand)
    supply_final.append(fictional_supply)
    supply_names_final.append("DF (Fikcyjny)")
    z = np.vstack([z, np.zeros((1, len(demand_final)))])

    # Nacisk - wykreślanie i wymuszanie tras
    for j in range(n_d):
            match pressure[j]:
                case "Wymuś":
                    z[n_s][j] = -1e9
                case "Wykreśl":
                    for i in range(n_s):
                        z[i][j] = -1e9
                case "Normalny priorytet" | _:
                    continue


    return z, supply_final, demand_final, supply_names_final, demand_names_final


# Tab 3: Rozwiązanie
with tabs[2]:
    st.subheader("Rozwiąż zagadnienie pośrednika")

    if st.button("Oblicz plan", type="primary", width='stretch'):
        supply = st.session_state.supply_df["Podaż"].tolist()
        demand = st.session_state.demand_df["Popyt"].tolist()
        buy_cost = st.session_state.buy_cost_df["Koszt zakupu"].tolist()
        sell_price = st.session_state.sell_price_df["Cena sprzedaży"].tolist()

        transport = st.session_state.transport_df.values
        #blocked = st.session_state.blocked_df.values
        pressure = st.session_state.customer_settings_df["Nacisk"].tolist()

        supply_names = st.session_state.supply_df["Dostawca"].tolist()
        demand_names = st.session_state.demand_df["Odbiorca"].tolist()

        z, supply_final, demand_final, supply_names_final, demand_names_final = (
            prepare_with_fictitious(
                supply,
                demand,
                buy_cost,
                sell_price,
                transport,
                supply_names,
                demand_names,
                pressure
            )
        )

        col1, col2, col3 = st.columns(3)

        col2.info(f"Bilans: podaż = {sum(supply)}, popyt = {sum(demand)}")
        col3.info(
            f"Dodano fikcyjnego odbiorcę (popyt={demand_final[-1]}) i fikcyjnego dostawcę (podaż={supply_final[-1]})"
        )

        with st.spinner("Obliczanie optymalnego planu..."):
            allocation, history, deltas_history, total_profit = solve_intermediary(
                z, supply_final, demand_final
            )

        col1.success(f"**Maksymalny całkowity zysk: {total_profit:,.2f}**")

        st.subheader("Optymalny plan dostaw")
        df_result = pd.DataFrame(
            allocation, index=supply_names_final, columns=demand_names_final
        )
        st.dataframe(df_result.style.format("{:.0f}"), width='stretch')

        st.subheader("Macierz zysku jednostkowego")
        df_z = pd.DataFrame(z, index=supply_names_final, columns=demand_names_final)
        st.dataframe(df_z.style.format("{:.2f}"), width='stretch')

        st.subheader("Iteracje algorytmu")

        for it, alloc in enumerate(history):
            is_optimal = it == len(history) - 1

            df_iter = pd.DataFrame(
                alloc, index=supply_names_final, columns=demand_names_final
            )

            with st.expander(
                f"Iteracja {it + 1}" + (" - OPTYMALNA" if is_optimal else "")
            ):
                st.dataframe(df_iter.style.format("{:.0f}"), width='stretch')

                if it < len(deltas_history):
                    _, deltas, max_d = deltas_history[it]

                    df_deltas = pd.DataFrame(
                        deltas, index=supply_names_final, columns=demand_names_final
                    )
                    st.write(f"**Maksymalna Δ = {max_d:.4f}**")
                    st.dataframe(
                        df_deltas.style.format("{:.2f}"), width='stretch'
                    )

                    if max_d < 0:
                        st.info("Brak dodatnich Δ – rozwiązanie optymalne")

        st.subheader("Podsumowanie")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Podaż rzeczywista", f"{sum(supply)}")
            st.metric("Podaż fikcyjna", f"{supply_final[-1]}")
            st.metric("Podaż całkowita", f"{sum(supply_final)}")
        with col2:
            st.metric("Popyt rzeczywisty", f"{sum(demand)}")
            st.metric("Popyt fikcyjny", f"{demand_final[-1]}")
            st.metric("Popyt całkowity", f"{sum(demand_final)}")
        with col3:
            st.metric("Liczba iteracji", f"{len(history)}")
            st.metric("Maksymalny zysk", f"{total_profit:,.2f}")


with tabs[3]:
    st.subheader("Opis działania programu")
    col1, col2 = st.columns(2)
    with col1:
        st.text("\nProgram służy do rozwiązywania zagadnienia transportowego pośrednika dla wprowadzanych danych dostawców, odbiorców, kosztów transportu i priorytetów odbiorców. " \
        "Istotą zagadnienia jest takie rozłożenie transportu między określonymi dostawcami a odbiorcami, aby zysk z transportu był dla pośrednika kupującego od danych dostawców i sprzedającego danym odbiorcom jak najwyższy. " \
        "\n\n" \
        "Uwzględnione mogą być również pewne naciski takie jak kontrakty o całkowitym zaspokojeniu popytu danego odbiorcy. " \
        "Można też uwzględnić całkowitą blokadę odbiorcy, co sprawi, że cała dostawa dla niego spadnie na fikcyjnego dostawcę. " \
        "Narzędzia te są dostępne w sekcji \"Blokada tras\". " \
        "Ta wersja programu nie uwzględnie blokad i priorytetów na dostawcach. " \
        "\n\n" \
        "Program wykorzystuje podczas obliczeń metodę wierzchołka północno-zachodniego. Określa ona kolejność dobierania tras wewnątrz bloków o danym priorytecie. " \
        "Wybierana jest najpierw trasa w górnym lewym rogu bloku, następnie zaś wybierane są kolejno trasy sąsienie po prawej lub poniżej, zależnie od tego czy zużyty został popyt czy podaż. " \
        "Aby zrównoważyć całkowity popyt i podaż dla wariantów niezbilansowanych dodani są fikcyjni dostawcy i odbiorcy. Zawsze mają oni najniższy priorytet. " \
        "Program pozwala przeanalizować cały proces obliczeniowy dzięki możliwości analizy tabel będących wynikami kolejnych iteracji algorytmu. " \
        "W tym programie uwzględnia się tylko zagadnienie pojedynczego pośrednika z bezpośrednimi dostawami od dostawców do odbiorców. " \
        "\n\n" \
        "Aby przeprowadzić obliczenia najpierw uzupełnij dane w sekcji \"Dane dostawców i odbiorców\". " \
        "Tabele zawierają już pewne przykładowe dane. Dla zaawansowanych badań można podawać ujemne popyt, podaż, ceny i koszta. Nazwy dostawców i odbiorców muszą być unikatowe i mieć przynajmniej 1 znak. " \
        "Dane, które wprowadzasz nie zostaną wprowadzone do systemu a inne tabele nie zostaną o nie zaktualizowane dopóki nie zatwierdzisz zmian. " \
        "Zatwierdzenie zmian w tabelach dotyczącyh odbiorców lub dostawców spowoduje utratę niezatwierdzonyc zmian w tabelach używających tych danych, jeśli liczba odbiorców lub dostawców ulegnie zmianie. " \
        "Aby usunąć dostawców lub odbiorców zaznacz ich w komórkach lewej kolumny danej tabeli a następnie wciśniej klawisz DELETE. Możesz anulować wprowadzone zmiany klikając odpowiedni przycisk. " \
        "Po wypełnieniu danych możesz wejść do sekcji \"Blokada tras\" i wybrać naciski na wybranych odbiorców. Opisy poszczególnych nacisków znajdują się w rozwijanej legndzie tej sekcji. " \
        "\n\n" \
        "Gdy wszystkie dane będą gotowe wejdź do sekcji \"Rozwiązanie\" i kliknij przycisk \"Oblicz plan\". Uzyskasz optymalny plan dostaw z najlepszym zyskiem dla zadanych nacisków. " \
        "Będziesz mieć też rozwijany wgląd w wyniki w kolejnych iteracjach algorytmu. Na dole strony znajdzie się podsumowanie z kluczowymi wartościami liczbowymi." \
        "\n\n" \
        "Życzymy miłego użytkowania!" \
        "\n\n" \
        "\nProjekt wykorzystuje framework Streamlit." \
        "\n\n" \
        "")
