# app.py
import numpy as np
import pandas as pd
import streamlit as st

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

# ============================================================
# ALGORYTM ZAGADNIENIA POŚREDNIKA (METODA PÓŁNOCNO-ZACHODNIA)
# ============================================================


def north_west_corner(supply, demand):
    """Rozwiązanie początkowe – metoda NW"""
    n_supply = len(supply)
    n_demand = len(demand)
    allocation = np.zeros((n_supply, n_demand))
    supply_left = supply.copy()
    demand_left = demand.copy()

    i, j = 0, 0
    while i < n_supply and j < n_demand:
        x = min(supply_left[i], demand_left[j])
        allocation[i, j] = x
        supply_left[i] -= x
        demand_left[j] -= x

        if supply_left[i] == 0:
            i += 1
        if demand_left[j] == 0:
            j += 1
    return allocation


def compute_potentials(z, allocation, n_supply, n_demand):
    """Wyznacz α i β z równań: z_ij - α_i - β_j = 0 dla tras bazowych"""
    alpha = [None] * n_supply
    beta = [None] * n_demand
    alpha[0] = 0
    changed = True

    while changed:
        changed = False
        for i in range(n_supply):
            for j in range(n_demand):
                if allocation[i][j] > 0:
                    if alpha[i] is not None and beta[j] is None:
                        beta[j] = z[i][j] - alpha[i]
                        changed = True
                    if beta[j] is not None and alpha[i] is None:
                        alpha[i] = z[i][j] - beta[j]
                        changed = True
    return alpha, beta


def compute_deltas(z, alpha, beta, allocation, n_supply, n_demand):
    """Δ_ij = z_ij - α_i - β_j dla komórek niebazowych"""
    deltas = np.full((n_supply, n_demand), -np.inf)
    for i in range(n_supply):
        for j in range(n_demand):
            if allocation[i][j] == 0 and alpha[i] is not None and beta[j] is not None:
                deltas[i][j] = z[i][j] - alpha[i] - beta[j]
    return deltas


def find_cycle(allocation, start_i, start_j, n_supply, n_demand):
    """Znajdź cykl korekcyjny dla danej komórki"""
    for i in range(n_supply):
        if i != start_i and allocation[i][start_j] > 0:
            for j in range(n_demand):
                if j != start_j and allocation[start_i][j] > 0 and allocation[i][j] > 0:
                    return [(start_i, start_j), (i, start_j), (i, j), (start_i, j)]
    return None


def improve_solution(allocation, cycle):
    """Poprawa rozwiązania – przesunięcie w cyklu (+ - + -)"""
    if not cycle:
        return allocation
    values = [allocation[i][j] for (i, j) in cycle[1::2]]
    min_val = min(values)

    for idx, (i, j) in enumerate(cycle):
        if idx % 2 == 0:
            allocation[i][j] += min_val
        else:
            allocation[i][j] -= min_val
    return allocation


def solve_intermediary(z, supply, demand, max_iter=100):
    """Rozwiązuje zagadnienie pośrednika (maksymalizacja)"""
    n_supply, n_demand = z.shape
    allocation = north_west_corner(supply, demand)
    history = [allocation.copy()]
    iterations_deltas = []

    for it in range(max_iter):
        alpha, beta = compute_potentials(z, allocation, n_supply, n_demand)
        deltas = compute_deltas(z, alpha, beta, allocation, n_supply, n_demand)

        max_delta = np.max(deltas)
        iterations_deltas.append((it, deltas.copy(), max_delta))

        if max_delta <= 1e-9:
            break

        pos = np.argwhere(deltas == max_delta)[0]
        i0, j0 = pos[0], pos[1]

        cycle = find_cycle(allocation, i0, j0, n_supply, n_demand)
        if cycle:
            allocation = improve_solution(allocation, cycle)
            history.append(allocation.copy())

    total_profit = np.sum(allocation * z)
    return allocation, history, iterations_deltas, total_profit


# ============================================================
# FUNKCJE SYNCHRONIZACJI DANYCH
# ============================================================


def sync_supply_data():
    """Synchronizuje koszty zakupu i macierz transportu z listą dostawców"""
    current_suppliers = st.session_state.supply_df["Dostawca"].tolist()

    # Synchronizacja kosztów zakupu
    current_buy = st.session_state.buy_cost_df
    current_buy_suppliers = current_buy["Dostawca"].tolist()

    if current_buy_suppliers != current_suppliers:
        new_buy = pd.DataFrame({"Dostawca": current_suppliers, "Koszt zakupu": 0})
        for i, supplier in enumerate(current_buy_suppliers):
            if supplier in current_suppliers:
                idx = current_suppliers.index(supplier)
                new_buy.loc[idx, "Koszt zakupu"] = current_buy.iloc[i, 1]
        st.session_state.buy_cost_df = new_buy

    # Synchronizacja macierzy transportu (wiersze)
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

    # Synchronizacja blokad (wiersze)
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

    # Synchronizacja cen sprzedaży
    current_sell = st.session_state.sell_price_df
    current_sell_customers = current_sell["Odbiorca"].tolist()

    if current_sell_customers != current_customers:
        new_sell = pd.DataFrame({"Odbiorca": current_customers, "Cena sprzedaży": 0})
        for i, customer in enumerate(current_sell_customers):
            if customer in current_customers:
                idx = current_customers.index(customer)
                new_sell.loc[idx, "Cena sprzedaży"] = current_sell.iloc[i, 1]
        st.session_state.sell_price_df = new_sell

    # Synchronizacja macierzy transportu (kolumny)
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

    # Synchronizacja blokad (kolumny)
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

# UI

st.title("Zagadnienie pośrednika")

tabs = st.tabs(
    [
        "Dane dostawców i odbiorców",
        "Blokowanie tras",
        "Rozwiązanie",
    ]
)

with tabs[0]:
    col1, col2 = st.columns(2)

    # KOLUMNA LEWA
    with col1:
        st.subheader("Podaż dostawców")
        edited_supply = st.data_editor(
            st.session_state.supply_df,
            num_rows="dynamic",
            use_container_width=True,
            key="supply_editor",
        )
        if not edited_supply.equals(st.session_state.supply_df):
            st.session_state.supply_df = edited_supply
            sync_supply_data()

        st.subheader("Koszty zakupu")
        edited_buy = st.data_editor(
            st.session_state.buy_cost_df,
            num_rows="fixed",
            use_container_width=True,
            key="buy_editor",
        )
        st.session_state.buy_cost_df = edited_buy

    # KOLUMNA PRAWA
    with col2:
        st.subheader("Popyt odbiorców")
        edited_demand = st.data_editor(
            st.session_state.demand_df,
            num_rows="dynamic",
            use_container_width=True,
            key="demand_editor",
        )
        if not edited_demand.equals(st.session_state.demand_df):
            st.session_state.demand_df = edited_demand
            sync_demand_data()

        st.subheader("Ceny sprzedaży")
        edited_sell = st.data_editor(
            st.session_state.sell_price_df,
            num_rows="fixed",
            use_container_width=True,
            key="sell_editor",
        )
        st.session_state.sell_price_df = edited_sell

    st.subheader("Koszty transportu")

    # Upewnij się, że macierz jest zsynchronizowana przed wyświetleniem
    current_suppliers = st.session_state.supply_df["Dostawca"].tolist()
    current_customers = st.session_state.demand_df["Odbiorca"].tolist()

    if (
        st.session_state.transport_df.index.tolist() != current_suppliers
        or st.session_state.transport_df.columns.tolist() != current_customers
    ):
        new_transport = pd.DataFrame(
            0, index=current_suppliers, columns=current_customers
        )
        old_transport = st.session_state.transport_df
        for i, row in enumerate(old_transport.index):
            if row in current_suppliers:
                for j, col in enumerate(old_transport.columns):
                    if col in current_customers:
                        new_transport.loc[row, col] = old_transport.iloc[i, j]
        st.session_state.transport_df = new_transport

    edited_transport = st.data_editor(
        st.session_state.transport_df, use_container_width=True, key="transport_editor"
    )
    st.session_state.transport_df = edited_transport

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
#         st.session_state.blocked_df, use_container_width=True, key="blocked_editor"
#     )
#     st.session_state.blocked_df = edited_blocked

#DOBÓR STATUSU NACISKU NA ODBIORCĘ:
#Wymuś - jak na zajęciach, sprowadza się do zablokowania fikcyjnego dostawcy dla tego odbiorcy i ustwienia temu odbiorcy wyższego priorytetu.
#Normalny priorytet - traktowanie domyślne.
#Ogranicz - niższy priorytet - obsługa pomiędzy normalnymi priorytetami, ale przed fikcyjnymi
#Wykreśl - całkowicie blokuje jakiekolwiek rzeczywiste dostawy do tego rzeczywistego odbiorcy.
#Na stan obecny zmiany w tabeli nie wpływają na obliczenia.
with tabs[1]:
    st.subheader("Blokowanie tras")

    current_customers = st.session_state.demand_df["Odbiorca"].unique().tolist()

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
            "Odbiorca": st.column_config.Column(disabled=True),
            "Nacisk": st.column_config.SelectboxColumn(
                "Nacisk",
                options=["Wymuś", "Normalny przydział", "Ogranicz", "Wykreśl"],
                required=True,
                default="Normalny przydział"
            )
        },
        use_container_width=True,
        hide_index=True,
        key="customer_settings_editor"
    )

    st.session_state.customer_settings_df = edited_settings


# rozwiązanie


def prepare_with_fictitious(
    supply, demand, buy_cost, sell_price, transport, blocked, supply_names, demand_names
):
    """Zawsze dodaje fikcyjnego dostawcę i fikcyjnego odbiorcę"""
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
            if blocked[i, j]:
                z[i, j] = -1e9

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

    return z, supply_final, demand_final, supply_names_final, demand_names_final


# Tab 3: Rozwiązanie
with tabs[2]:
    st.subheader("Rozwiąż zagadnienie pośrednika")

    if st.button("Oblicz plan", type="primary", use_container_width=True):
        supply = st.session_state.supply_df["Podaż"].tolist()
        demand = st.session_state.demand_df["Popyt"].tolist()
        buy_cost = st.session_state.buy_cost_df["Koszt zakupu"].tolist()
        sell_price = st.session_state.sell_price_df["Cena sprzedaży"].tolist()

        transport = st.session_state.transport_df.values
        blocked = st.session_state.blocked_df.values

        supply_names = st.session_state.supply_df["Dostawca"].tolist()
        demand_names = st.session_state.demand_df["Odbiorca"].tolist()

        z, supply_final, demand_final, supply_names_final, demand_names_final = (
            prepare_with_fictitious(
                supply,
                demand,
                buy_cost,
                sell_price,
                transport,
                blocked,
                supply_names,
                demand_names,
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
        st.dataframe(df_result.style.format("{:.0f}"), use_container_width=True)

        st.subheader("Macierz zysku jednostkowego")
        df_z = pd.DataFrame(z, index=supply_names_final, columns=demand_names_final)
        st.dataframe(df_z.style.format("{:.2f}"), use_container_width=True)

        st.subheader("Iteracje algorytmu")

        for it, alloc in enumerate(history):
            is_optimal = it == len(history) - 1

            df_iter = pd.DataFrame(
                alloc, index=supply_names_final, columns=demand_names_final
            )

            with st.expander(
                f"Iteracja {it + 1}" + (" - OPTYMALNA" if is_optimal else "")
            ):
                st.dataframe(df_iter.style.format("{:.0f}"), use_container_width=True)

                if it < len(deltas_history):
                    _, deltas, max_d = deltas_history[it]

                    df_deltas = pd.DataFrame(
                        deltas, index=supply_names_final, columns=demand_names_final
                    )
                    st.write(f"**Maksymalna Δ = {max_d:.4f}**")
                    st.dataframe(
                        df_deltas.style.format("{:.2f}"), use_container_width=True
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
