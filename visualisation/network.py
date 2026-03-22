import networkx as nx
import streamlit as st
from pyvis.network import Network
import tempfile

def show_graph(G):
    pos = nx.kamada_kawai_layout(G)

    net = Network(height="600px", width="100%", directed=True)
    net.toggle_physics(False)

    # Add nodes
    for node, data in G.nodes(data=True):
        x, y = pos[node]
        if data["type"] == "reaction":
            shape = "box"
        else:
            shape = "dot"
        label = node
        color = "red" if data.get("type") == "reaction" else "blue"
        net.add_node(
            node,
            x=x * 1000,
            y=y * 1000,
            label=label, 
            color=color,
            shape=shape,
            physics=False  # CRUCIAL
        )

    # Add edges
    for u, v in G.edges():
        net.add_edge(u, v)

    # Save to temp HTML
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(tmp_file.name)

    # Display in Streamlit
    with open(tmp_file.name, "r") as f:
        html = f.read()

    st.components.v1.html(html, height=600)

def cobra_to_bipartite_graph(model):
    G = nx.DiGraph()

    for rxn in model.reactions:
        G.add_node(rxn.id, type="reaction")

        for met, coeff in rxn.metabolites.items():
            G.add_node(met.id, type="metabolite")

            if coeff < 0:
                # metabolite consumed
                G.add_edge(met.id, rxn.id)
            else:
                # metabolite produced
                G.add_edge(rxn.id, met.id)

    return G

def extract_k_hop_subgraph(G, center_node, k=3):
    nodes = nx.single_source_shortest_path_length(G, center_node, cutoff=k).keys()
    return G.subgraph(nodes).copy()