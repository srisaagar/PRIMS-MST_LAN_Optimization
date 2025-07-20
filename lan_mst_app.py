from flask import Flask, render_template, request, jsonify, send_file
import networkx as nx
import json
import os
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

app = Flask(__name__)

# ✅ MODIFICATION: The graph is now initialized as empty.
# All nodes and edges must be added through the web interface.
graph = nx.Graph()

# --- Helper Functions for Consistent Styling ---
def get_title_font():
    """Returns a FontProperties object for a clean, modern title."""
    return FontProperties(family='sans-serif', weight='bold', size=18)

def get_label_font():
    """Returns a dictionary for stylish node and edge labels."""
    return {'font_family': 'sans-serif', 'font_weight': 'bold', 'font_size': 12}

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main page of the application."""
    # The provided HTML file is named 'index.html'
    return render_template('index.html')

@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    """Returns the list of current nodes to populate dropdowns on page load."""
    return jsonify(list(graph.nodes))

@app.route('/add_node', methods=['POST'])
def add_node():
    """Adds a new node to the graph."""
    node = request.get_json()['node']
    if node and node not in graph:
        graph.add_node(node)
        return jsonify({'status': 'Node added', 'nodes': list(graph.nodes)})
    return jsonify({'status': 'Node already exists or is invalid', 'nodes': list(graph.nodes)})

@app.route('/add_edge', methods=['POST'])
def add_edge():
    """Adds a weighted edge between two existing nodes."""
    data = request.get_json()
    u, v, weight = data['from'], data['to'], float(data['weight'])
    if u in graph and v in graph:
        graph.add_edge(u, v, weight=weight)
        return jsonify({'status': 'Edge added', 'edges': list(graph.edges(data=True))})
    return jsonify({'status': 'One or both nodes not found'})

@app.route('/calculate_mst', methods=['GET'])
def calculate_mst():
    """Calculates the Minimum Spanning Tree and its total cost."""
    if not graph:
        return jsonify({'mst': [], 'total_cost': 0})
    if not nx.is_connected(graph):
        return jsonify({'mst': [], 'total_cost': 0, 'error': 'Graph is not connected'}), 400
        
    mst = nx.minimum_spanning_tree(graph, algorithm='prim')
    edges = list(mst.edges(data=True))
    total_cost = sum(edge[2]['weight'] for edge in edges)
    return jsonify({'mst': edges, 'total_cost': total_cost})

@app.route('/export_json', methods=['GET'])
def export_json():
    """Exports the current graph to a JSON file."""
    os.makedirs('static', exist_ok=True)
    file_path = 'static/lan_network.json'
    with open(file_path, 'w') as f:
        json.dump(nx.node_link_data(graph), f, indent=4)
    return send_file(file_path, as_attachment=True)

@app.route('/export_txt', methods=['GET'])
def export_txt():
    """Exports the graph's edge list to a text file."""
    os.makedirs('static', exist_ok=True)
    file_path = 'static/pt_topology.txt'
    with open(file_path, 'w') as f:
        f.write("Edge List (Node1 -- Node2 [Weight])\n")
        f.write("-" * 35 + "\n")
        for u, v, data in graph.edges(data=True):
            f.write(f"{u} -- {v} [{data.get('weight', 'N/A')}m]\n")
    return send_file(file_path, as_attachment=True)

@app.route('/mst_image', methods=['GET'])
def mst_image():
    """Generates and returns an attractive image of the MST."""
    if not nx.is_connected(graph):
        return jsonify({'error': 'Graph is not connected, cannot generate image'}), 400
    if not graph:
        return jsonify({'error': 'Graph is empty'}), 400

    mst = nx.minimum_spanning_tree(graph)
    pos = nx.spring_layout(mst, seed=42, k=0.9)
    total_mst_cost = sum(data['weight'] for _, _, data in mst.edges(data=True))

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('#e9ecef')

    title_font = get_title_font()
    plt.title(f"Minimum Spanning Tree (MST)\nTotal Cost: ₹{total_mst_cost:,.2f}", fontproperties=title_font, color='#343a40')

    nx.draw_networkx_nodes(mst, pos, node_size=2500, node_color='black', alpha=0.2, ax=ax)
    nx.draw_networkx_nodes(mst, pos, node_size=2200, node_color='#74c69d', edgecolors='#2d6a4f', linewidths=2.5, ax=ax)
    nx.draw_networkx_edges(mst, pos, width=3.0, edge_color='#495057', alpha=0.8, ax=ax)
    
    label_font_dict = get_label_font()
    nx.draw_networkx_labels(mst, pos, font_color='#000000', **label_font_dict, ax=ax)
    edge_labels = nx.get_edge_attributes(mst, 'weight')
    nx.draw_networkx_edge_labels(mst, pos, edge_labels=edge_labels, font_color='#c9184a', font_size=10, font_weight='bold', ax=ax)

    os.makedirs('static', exist_ok=True)
    file_path = 'static/mst_graph.png'
    plt.tight_layout()
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return send_file(file_path, mimetype='image/png')

@app.route('/compare_graphs', methods=['GET'])
def compare_graphs():
    """Generates and returns a side-by-side comparison of the original graph and its MST."""
    if not nx.is_connected(graph):
        return jsonify({'error': 'Graph is not connected, cannot generate image'}), 400
    if not graph:
        return jsonify({'error': 'Graph is empty'}), 400

    pos = nx.spring_layout(graph, seed=42, k=0.9)
    mst = nx.minimum_spanning_tree(graph)
    total_graph_cost = sum(data.get('weight', 0) for _, _, data in graph.edges(data=True))
    total_mst_cost = sum(data.get('weight', 0) for _, _, data in mst.edges(data=True))

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    fig.patch.set_facecolor('#e9ecef')

    title_font = get_title_font()
    fig.suptitle("Original Network vs. Minimum Spanning Tree (MST)", fontproperties=title_font, color='#343a40')

    ax1.set_facecolor('#e9ecef')
    nx.draw(graph, pos, ax=ax1, with_labels=True, node_color='#69b3a2', edge_color='#adb5bd',
            node_size=2200, font_size=12, font_weight='bold', width=2.5)
    nx.draw_networkx_edge_labels(graph, pos, ax=ax1, edge_labels=nx.get_edge_attributes(graph, 'weight'),
                                 font_color='#5c5c5c', font_size=10, font_weight='bold')
    ax1.set_title(f"Original Network\nTotal Cost: ₹{total_graph_cost:,.2f}",
                  fontdict={'fontsize': 16, 'fontweight': 'bold', 'color': '#2a9d8f'})

    ax2.set_facecolor('#e9ecef')
    nx.draw(mst, pos, ax=ax2, with_labels=True, node_color='#f4a261', edge_color='#e76f51',
            node_size=2200, font_size=12, font_weight='bold', width=3)
    nx.draw_networkx_edge_labels(mst, pos, ax=ax2, edge_labels=nx.get_edge_attributes(mst, 'weight'),
                                 font_color='#c9184a', font_size=10, font_weight='bold')
    ax2.set_title(f"Minimum Spanning Tree\nTotal Cost: ₹{total_mst_cost:,.2f}",
                  fontdict={'fontsize': 16, 'fontweight': 'bold', 'color': '#e76f51'})

    os.makedirs('static', exist_ok=True)
    file_path = 'static/mst_comparison.png'
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return send_file(file_path, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)