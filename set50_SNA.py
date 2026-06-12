import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import json
from pathlib import Path

plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="SET50 Shareholder Relationship Graph", layout="wide")
st.title("SET50 Shareholder Relationship Network")

DATA_PATH = Path(__file__).parent / "set50_shareholders_1346.json"

@st.cache_data
def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# Build a short label for each shareholder
def short_label(name, max_len=20):
    if len(name) <= max_len:
        return name
    # Use last word as short identifier
    parts = name.strip().split()
    if len(parts) >= 2:
        return parts[-1][:max_len]
    return name[:max_len]

shareholder_label = {}
for item in data:
    n = item["name"]
    if n not in shareholder_label:
        shareholder_label[n] = short_label(n)

# Build graph with short labels as node names
G = nx.Graph()
shareholders = {}

for item in data:
    sym = item["symbol"]
    name = item["name"]
    label = shareholder_label[name]
    pct = item["percent"]

    G.add_node(sym, type="company", full_name=sym)
    G.add_node(label, type="shareholder", full_name=name)
    G.add_edge(label, sym, weight=pct, percent=pct, full_name=name)

    if label not in shareholders:
        shareholders[label] = {"full_name": name, "companies": {}}
    shareholders[label]["companies"][sym] = pct

st.sidebar.header("Filters")
min_pct = st.sidebar.slider("Minimum ownership %", 0.0, 50.0, 1.0, 0.5)

companies = sorted([n for n, d in G.nodes(data=True) if d["type"] == "company"])
sh_labels = sorted(shareholders.keys())

selected_company = st.sidebar.selectbox("Filter by company", ["All"] + companies)
selected_shareholder = st.sidebar.selectbox("Filter by shareholder", ["All"] + sh_labels)

st.sidebar.markdown("---")
st.sidebar.subheader("Network Stats")
st.sidebar.write(f"Total companies: {len(companies)}")
st.sidebar.write(f"Total shareholders: {len(shareholders)}")
st.sidebar.write(f"Total relationships: {len(data)}")

edges_to_keep = [
    (u, v) for u, v, d in G.edges(data=True) if d["percent"] >= min_pct
]
H = G.edge_subgraph(edges_to_keep).copy()

if selected_company != "All":
    nodes_to_keep = {selected_company}
    for n in H.neighbors(selected_company):
        nodes_to_keep.add(n)
    H = H.subgraph(nodes_to_keep).copy()

if selected_shareholder != "All":
    nodes_to_keep = {selected_shareholder}
    for n in H.neighbors(selected_shareholder):
        nodes_to_keep.add(n)
    H = H.subgraph(nodes_to_keep).copy()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Relationship Graph")

    if H.number_of_nodes() == 0:
        st.info("No relationships match the current filters.")
    else:
        fig, ax = plt.subplots(figsize=(14, 10))
        pos = nx.spring_layout(H, seed=42, k=2, iterations=50)

        company_nodes = [n for n, d in H.nodes(data=True) if d["type"] == "company"]
        shareholder_nodes = [n for n, d in H.nodes(data=True) if d["type"] == "shareholder"]

        nx.draw_networkx_nodes(
            H, pos, nodelist=company_nodes, node_color="#ff6b6b",
            node_size=600, label="Companies", ax=ax
        )
        nx.draw_networkx_nodes(
            H, pos, nodelist=shareholder_nodes, node_color="#4ecdc4",
            node_size=300, label="Shareholders", ax=ax
        )

        weights = [d["percent"] for _, _, d in H.edges(data=True)]
        min_w, max_w = min(weights), max(weights)
        edge_widths = [1 + 3 * (w - min_w) / (max_w - min_w + 0.001) for w in weights]

        nx.draw_networkx_edges(
            H, pos, width=edge_widths, alpha=0.5, edge_color="#888888", ax=ax
        )

        nx.draw_networkx_labels(H, pos, font_size=7, ax=ax)

        ax.legend(fontsize=10, loc="upper right")
        ax.set_title("SET50 Shareholder Relationships (edge width = ownership %)", fontsize=14)
        ax.axis("off")
        st.pyplot(fig)

with col2:
    st.subheader("Top Shareholders")
    all_items = []
    for item in data:
        all_items.append((item["name"], item["percent"], item["symbol"]))
    all_items.sort(key=lambda x: x[1], reverse=True)

    for name, pct, sym in all_items[:20]:
        st.write(f"- {sym} ← {name}: **{pct:.2f}%**")

    st.markdown("---")
    st.subheader("Hover Guide")
    st.write("Shareholder labels in the graph are abbreviated. Full names:")
    for label, info in list(shareholders.items())[:15]:
        if label != info["full_name"]:
            st.caption(f"**{label}** → {info['full_name']}")

    st.markdown("---")
    st.subheader("Most Connected Shareholders")
    degree_centrality = nx.degree_centrality(H)
    sh_centrality = {
        n: v for n, v in degree_centrality.items()
        if n in H.nodes and H.nodes[n].get("type") == "shareholder"
    }
    for name, cent in sorted(sh_centrality.items(), key=lambda x: x[1], reverse=True)[:10]:
        st.write(f"- {name}: centrality = {cent:.3f}")

    st.markdown("---")
    st.subheader("SNA Metrics")
    if H.number_of_nodes() > 0:
        comps = list(nx.connected_components(H))
        st.write(f"Connected components: {len(comps)}")
        if comps:
            st.write(f"Largest component size: {len(max(comps, key=len))}")
        if H.number_of_nodes() > 1:
            try:
                diam = nx.diameter(H.subgraph(max(comps, key=len)))
                st.write(f"Diameter (largest comp): {diam}")
            except nx.NetworkXError:
                pass

    st.markdown("---")
    st.subheader("Relationship Table")
    table_data = []
    for item in data:
        if item["percent"] >= min_pct:
            table_data.append({
                "Company": item["symbol"],
                "Shareholder": item["name"],
                "%": f"{item['percent']:.2f}%"
            })
    if table_data:
        st.dataframe(table_data, use_container_width=True, hide_index=True)
