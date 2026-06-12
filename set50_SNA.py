import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
from pathlib import Path

plt.rcParams["axes.unicode_minus"] = False

# --- Thai font support ---
FONT_PATH = Path(__file__).parent / "fonts" / "NotoSansThai-Regular.ttf"
if FONT_PATH.exists():
    fm.fontManager.addfont(str(FONT_PATH))
    thai_font_name = fm.FontProperties(fname=str(FONT_PATH)).get_name()
    plt.rcParams["font.family"] = thai_font_name
else:
    thai_font_name = None
    st.warning(
        "Thai font not found at fonts/NotoSansThai-Regular.ttf — "
        "Thai labels in the graph may not render correctly. "
        "Download Noto Sans Thai from Google Fonts and place it in a 'fonts' folder in your repo."
    )

st.set_page_config(page_title="SET50 Shareholder Relationship Graph", layout="wide")
st.title("SET50 Shareholder Relationship Network")

DATA_PATH = Path(__file__).parent / "set50_shareholders_1346.json"

@st.cache_data
def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# Build shareholder ID mapping (ASCII-only IDs)
shareholder_info = {}
sid_map = {}  # name -> sid
sid = 1
for item in data:
    n = item["name"]
    if n not in sid_map:
        sid_map[n] = f"SH{sid:03d}"
        shareholder_info[sid_map[n]] = {"full_name": n}
        sid += 1

# Build graph with ASCII node names
G = nx.Graph()
companies = set()

for item in data:
    sym = item["symbol"]
    name = item["name"]
    sh_id = sid_map[name]
    pct = item["percent"]
    companies.add(sym)
    G.add_node(sym, type="company")
    G.add_node(sh_id, type="shareholder")
    G.add_edge(sh_id, sym, weight=pct, percent=pct)

st.sidebar.header("Filters")
min_pct = st.sidebar.slider("Minimum ownership %", 0.0, 50.0, 1.0, 0.5)
selected_company = st.sidebar.selectbox("Filter by company", ["All"] + sorted(companies))
selected_sh = st.sidebar.selectbox("Filter by shareholder", ["All"] + sorted(shareholder_info.keys(),
    key=lambda x: shareholder_info[x]["full_name"]))

st.sidebar.markdown("---")
st.sidebar.subheader("Network Stats")
st.sidebar.write(f"Companies: {len(companies)}")
st.sidebar.write(f"Shareholders: {len(shareholder_info)}")
st.sidebar.write(f"Relationships: {len(data)}")

edges_to_keep = [(u, v) for u, v, d in G.edges(data=True) if d["percent"] >= min_pct]
H = G.edge_subgraph(edges_to_keep).copy()

if selected_company != "All" and selected_company in H:
    ns = {selected_company} | set(H.neighbors(selected_company))
    H = H.subgraph(ns).copy()

if selected_sh != "All" and selected_sh in H:
    ns = {selected_sh} | set(H.neighbors(selected_sh))
    H = H.subgraph(ns).copy()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Relationship Graph")
    if H.number_of_nodes() == 0:
        st.info("No relationships match the current filters.")
    else:
        fig, ax = plt.subplots(figsize=(14, 10))
        pos = nx.spring_layout(H, seed=42, k=2, iterations=50)

        cn = [n for n, d in H.nodes(data=True) if d["type"] == "company"]
        sn = [n for n, d in H.nodes(data=True) if d["type"] == "shareholder"]

        nx.draw_networkx_nodes(H, pos, nodelist=cn, node_color="#ff6b6b", node_size=600, label="Companies", ax=ax)
        nx.draw_networkx_nodes(H, pos, nodelist=sn, node_color="#4ecdc4", node_size=300, label="Shareholders", ax=ax)

        weights = [d["percent"] for _, _, d in H.edges(data=True)]
        mn, mx = min(weights), max(weights)
        ew = [1 + 3 * (w - mn) / (mx - mn + 0.001) for w in weights]
        nx.draw_networkx_edges(H, pos, width=ew, alpha=0.5, edge_color="#888888", ax=ax)

        # Use Thai shareholder names for shareholder node labels, symbols for companies
        labels = {
            n: (shareholder_info[n]["full_name"] if d["type"] == "shareholder" else n)
            for n, d in H.nodes(data=True)
        }
        label_kwargs = {"font_size": 7, "ax": ax}
        if thai_font_name:
            label_kwargs["font_family"] = thai_font_name
        nx.draw_networkx_labels(H, pos, labels=labels, **label_kwargs)

        ax.legend(fontsize=10, loc="upper right")
        ax.set_title("SET50 Shareholder Relationships (edge width = ownership %)", fontsize=14)
        ax.axis("off")
        st.pyplot(fig)

with col2:
    st.subheader("Top Ownership Stakes")
    rows = sorted(data, key=lambda x: x["percent"], reverse=True)[:20]
    for r in rows:
        st.write(f"- {r['symbol']} ← {r['name']}: **{r['percent']:.2f}%**")

    st.markdown("---")
    st.subheader("Shareholder ID Map")
    for sid, info in sorted(shareholder_info.items(), key=lambda x: x[1]["full_name"])[:20]:
        st.caption(f"**{sid}** → {info['full_name']}")

    st.markdown("---")
    st.subheader("Most Connected Shareholders")
    dc = nx.degree_centrality(H)
    top_sh = sorted([(n, v) for n, v in dc.items() if n in H.nodes and H.nodes[n].get("type") == "shareholder"],
                    key=lambda x: x[1], reverse=True)[:10]
    for sid, cent in top_sh:
        st.write(f"- {sid} ({shareholder_info.get(sid, {}).get('full_name', sid)}): centrality = {cent:.3f}")

    st.markdown("---")
    st.subheader("SNA Metrics")
    if H.number_of_nodes() > 0:
        comps = list(nx.connected_components(H))
        st.write(f"Connected components: {len(comps)}")
        if comps:
            st.write(f"Largest component size: {len(max(comps, key=len))}")
        if H.number_of_nodes() > 1:
            try:
                st.write(f"Diameter (largest comp): {nx.diameter(H.subgraph(max(comps, key=len)))}")
            except nx.NetworkXError:
                pass

    st.markdown("---")
    st.subheader("All Relationships")
    tbl = [{"Company": r["symbol"], "Shareholder ID": sid_map[r["name"]],
            "Shareholder Name": r["name"], "%": f"{r['percent']:.2f}%"}
           for r in data if r["percent"] >= min_pct]
    if tbl:
        st.dataframe(tbl, use_container_width=True, hide_index=True)
