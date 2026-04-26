import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO


#Obliczanie (ES, EF, LS, LF)

def compute_cpm(G: nx.DiGraph) -> dict:
    if not G.nodes:
        return {}
    #zbiera czasy trwania operacji
    duration = {}
    for i in G.nodes:
        duration[i] = G.nodes[i].get("d", 0)
    #Operacje w kolejności topologicznej
    topolist = list(nx.topological_sort(G))

    #Early start i Early Finish
    ES = {}
    EF = {}
    for i in topolist:
        pre = list(G.predecessors(i))
    
        if len(pre) == 0:
            ES[i] = 0
        else:
            mozliwe_starty = []
            for p in pre:
                mozliwe_starty.append(EF[p])
            ES[i] = max(mozliwe_starty)
        EF[i] = ES[i] + duration[i]

    project_end = max(EF.values())

    #Late start i Late Finish
    LF = {}
    LS = {}
    for i in reversed(topolist):
        post = list(G.successors(i))
        if len(post) == 0:
            LF[i] = project_end
        else:
            mozliwe_konce = []
            for s in post:
                mozliwe_konce.append(ES[s])
            LF[i] = min(mozliwe_konce)
        LS[i] = LF[i] - duration[i]

    result = {}
    for i in topolist:
        result[i] = {
            "ES": ES[i],
            "EF": EF[i],
            "LS": LS[i],
            "LF": LF[i],
            "TF": LS[i] - ES[i],
        }
    return result

def gantt_chart(G: nx.DiGraph) -> BytesIO | None:
    if not G or not G.nodes:
        return None

    cpm = compute_cpm(G)
    if not cpm:
        return None

    # Sortowanie czynności według ES, potem nazwy
    tasks = sorted(cpm.keys(), key=lambda n: (cpm[n]["ES"], n))
    n_tasks = len(tasks)
    project_end = max(v["LF"] for v in cpm.values())


    bar_h  = 0.5   # wysokość paska zadania
    y_gap  = 1.0   # odstęp między wierszami

    graph_height = max(4, n_tasks * y_gap + 1.5) # wysokość wykresu
    #okno i obszar rysowania
    fig, ax = plt.subplots(figsize=(12, graph_height), facecolor="#fbfcfd")
    ax.set_facecolor("#fbfcfd")

    for i, task in enumerate(tasks):
        info = cpm[task]
        y = (n_tasks - 1 - i) * y_gap   # oś Y od góry
        es, ef = info["ES"], info["EF"]
        ls, lf = info["LS"], info["LF"]
        tf     = info["TF"]
        dur    = G.nodes[task].get("d", 0)
        is_critical = (tf == 0)

        bar_color = "#EF4444" if is_critical else "#1E3A8A" 

        # Pasek ES→EF (realizacja)
        ax.barh(y, ef - es, left=es, height=bar_h,
                color=bar_color, edgecolor="black", linewidth=0.5,
                align="center", zorder=3)

        # Pasek zapasu czasu EF→LF (float)
        if tf > 0:
            ax.barh(y, tf, left=ef, height=bar_h * 0.4,
                    color="#334155", edgecolor="#64748B", linewidth=0.4,
                    align="center", zorder=2, hatch="//", alpha=0.7)

        # Etykieta na pasku: nazwa + czas
        ax.text(es + (ef - es) / 2, y, f"{task} ({dur})",
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="black", zorder=4)

        # Etykiety ES / EF po bokach
        ax.text(es - 0.1, y, str(es), ha="right", va="center",
                fontsize=7, color="#94A3B8")
        ax.text(ef + 0.1 + (tf if tf > 0 else 0), y, str(lf),
                ha="left", va="center", fontsize=7, color="#94A3B8")

    # --- Oś X i siatka ---
    ax.set_xlim(-0.5, project_end + 1)
    ax.set_ylim(-y_gap, n_tasks * y_gap)
    ax.set_yticks([])

    ax.set_xticks(range(0, int(project_end) + 2))
    ax.tick_params(axis="x", colors="#94A3B8", labelsize=8)
    ax.xaxis.label.set_color("#94A3B8")
    ax.set_xlabel("Czas", color="#94A3B8", fontsize=9)

    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2530")

    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color="#1e2530", linewidth=0.7, linestyle="--", zorder=0)

    # --- Legenda ---
    legend_elements = [
        mpatches.Patch(facecolor="#EF4444", edgecolor="black", label="Ścieżka krytyczna (TF=0)"),
        mpatches.Patch(facecolor="#1E3A8A" ,   edgecolor="black", label="Czynność zwykła"),
        mpatches.Patch(facecolor="#334155", edgecolor="#64748B",
                       hatch="//", alpha=0.7, label="Zapas czasu (TF)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right",
              facecolor="#1e2530", edgecolor="#334155",
              labelcolor="black", fontsize=8)

    ax.set_title("Wykres Gantta (CPM)", color="black", fontsize=12, pad=10)

    fig.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", transparent=False, dpi=130,
                bbox_inches="tight", facecolor="#fbfcfd")
    plt.close()
    return buf