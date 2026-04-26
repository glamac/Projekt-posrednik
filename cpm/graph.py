import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

def generate_cpm_graph(G, title, is_aoa=False):
    if not G or not G.nodes: 
        return None
    
    # 2. Ustawienie wyglądu okna i tła
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0e1117')
    
    # 3. UKŁADANIE: Wyznaczanie 'warstw' (od lewej do prawej)
    # Przechodzimy przez graf w kolejności technologicznej
    for node in nx.topological_sort(G):
        predecessors = list(G.predecessors(node))
        # Jeśli brak poprzedników, warstwa = 0 (start). 
        # W przeciwnym razie warstwa to maks. warstwa poprzednika + 1
        G.nodes[node]['layer'] = 0 if not predecessors else max(G.nodes[p]['layer'] for p in predecessors) + 1
    
    # Multipartite_layout ustawia węzły w pionowych kolumnach na podstawie ich 'layer'
    pos = nx.multipartite_layout(G, subset_key="layer")

    # 4. RYSOWANIE: Wybór modelu wyświetlania
    if is_aoa:
        # Model AOA (Czynność na strzałce): Węzły to zdarzenia (koła)
        nx.draw(G, pos, with_labels=True, node_color="#007BFF", node_size=700, ax=ax)
        
        # Pobieranie i rysowanie etykiet czynności na krawędziach (strzałkach)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color="#BFDBFE", bbox=dict(alpha=0))
    else:
        # Model AON (Czynność w węźle): Węzły to zadania (kwadraty)
        # Przygotowanie etykiet z nazwą i czasem trwania (d)
        node_labels = {n: f"{n}\n({G.nodes[n].get('d', 0)})" for n in G.nodes}
        
        nx.draw(G, pos, with_labels=True, labels=node_labels, 
                node_shape="s", node_color="#1E3A8A", node_size=2000, font_color="white", ax=ax)

    # 5. FINALIZACJA: Estetyka i eksport do Streamlit
    ax.set_title(title, color="white")
    ax.axis('off') # Ukrycie osi wykresu
    
    buf = BytesIO()
    plt.savefig(buf, format="png", transparent=True)
    plt.close()
    return buf