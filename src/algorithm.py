import numpy as np
# Algorytm


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


def compute_potentials(z, base_ones, n_supply, n_demand):
    """Wyznacz α i β z równań: z_ij - α_i - β_j = 0 dla tras bazowych"""
    alpha = [None] * n_supply
    beta = [None] * n_demand

    alpha[0] = 0

    while None in alpha or None in beta:
        changed = False
        for i in range(n_supply):
            for j in range(n_demand):
                if base_ones[i, j]:
                    if alpha[i] is not None and beta[j] is None:
                        beta[j] = z[i, j] - alpha[i]
                        changed = True
                    elif beta[j] is not None and alpha[i] is None:
                        alpha[i] = z[i, j] - beta[j]
                        changed = True

        if not changed and (None in alpha or None in beta):
            found = False
            for i in range(n_supply):
                for j in range(n_demand):
                    if not base_ones[i, j]:
                        if (alpha[i] is not None and beta[j] is None) or \
                           (beta[j] is not None and alpha[i] is None):
                            base_ones[i, j] = True
                            found = True
                            break
                if found: break

    return alpha, beta, base_ones


def compute_deltas(z, alpha, beta, base_ones, n_supply, n_demand):
    """Δ_ij = z_ij - α_i - β_j dla komórek niebazowych"""
    deltas = np.full((n_supply, n_demand), -np.inf)
    for i in range(n_supply):
        for j in range(n_demand):
            if not base_ones[i][j] and alpha[i] is not None and beta[j] is not None:
                deltas[i][j] = z[i][j] - alpha[i] - beta[j]
    return deltas


def find_cycle(base_ones, start_i, start_j, n_supply, n_demand):
    """Znajdź cykl korekcyjny dla danej komórki"""
    for i in range(n_supply):
        if i != start_i and base_ones[i][start_j]:
            for j in range(n_demand):
                if j != start_j and base_ones[start_i][j] and base_ones[i][j]:
                    return [(start_i, start_j), (i, start_j), (i, j), (start_i, j)]
    return None


def improve_solution(allocation, base_ones, cycle):
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

    base_ones[cycle[0][0]][cycle[0][1]] = True
    removed = False
    for (i, j) in cycle[1::2]:
        if allocation[i][j] == 0:
            base_ones[i][j] = False
            removed = True
            break

    return allocation, base_ones


def solve_intermediary(z, supply, demand, max_iter=100):
    """Rozwiązuje zagadnienie pośrednika (maksymalizacja)"""
    n_supply, n_demand = z.shape
    allocation = north_west_corner(supply, demand)
    base_ones = (allocation > 0)
    history = [allocation.copy()]
    iterations_deltas = []

    for it in range(max_iter):
        alpha, beta, base_ones = compute_potentials(z, base_ones, n_supply, n_demand)
        deltas = compute_deltas(z, alpha, beta, base_ones, n_supply, n_demand)

        max_delta = np.max(deltas)
        iterations_deltas.append((it, deltas.copy(), max_delta))

        if max_delta < 0:
            break

        pos = np.argwhere(deltas == max_delta)[0]
        i0, j0 = pos[0], pos[1]

        cycle = find_cycle(base_ones, i0, j0, n_supply, n_demand)
        if cycle:
            allocation, base_ones = improve_solution(allocation, base_ones, cycle)
            history.append(allocation.copy())

    total_profit = np.sum(allocation * z)
    return allocation, history, iterations_deltas, total_profit
