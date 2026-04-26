import networkx as nx

class CPMManager:
    def __init__(self, df, mode):
        self.df = df
        self.mode = mode # 0 dla Poprzedników, 1 dla Następnych

    def build_aon(self):
        G = nx.DiGraph()
        for _, r in self.df.iterrows():
            task = str(r["Czynność"]).strip().upper()
            if not task: continue
            G.add_node(task, d=r.get("Czas", 0))
            
            col = "Poprzednicy" if self.mode == 0 else "Następstwo zdarzeń"
            rel = str(r.get(col, "")).strip()
            
            if rel and rel.lower() not in ["none", "nan", ""]:
                for target in rel.split(","):
                    t = target.strip().upper()
                    if self.mode == 0: G.add_edge(t, task)
                    else: G.add_edge(task, t)
        return G

    def build_aoa(self):
        G = nx.DiGraph()
        # Prosta wersja AOA dla celów wizualnych
        ends, nodes, start = {}, 1, 0
        for _, r in self.df.iterrows():
            task = str(r["Czynność"]).strip().upper()
            if not task: continue
            
            col = "Poprzednicy" if self.mode == 0 else "Następstwo zdarzeń"
            rel = str(r.get(col, "")).strip()
            preds = rel.split(",") if rel and rel.lower() not in ["none", "nan", ""] else []
            
            u = ends.get(preds[0].strip().upper(), start) if preds else start
            v = nodes
            G.add_edge(u, v, label=f"{task}({r.get('Czas', 0)})")
            ends[task], nodes = v, nodes + 1
        return G