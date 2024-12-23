import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import os
from PIL import Image
import base64
from tqdm import tqdm

@st.cache_data
def load_node_images(_nodes):
    nodes = list(_nodes)
    images = {}
    for node in tqdm(nodes, desc="Loading node images", leave=False):
        try:
            img_path = f"minecraft_item_images/{node}.png"
            if os.path.exists(img_path):
                with open(img_path, "rb") as img_file:
                    encoded_img = base64.b64encode(img_file.read()).decode()
                    images[node] = f"data:image/png;base64,{encoded_img}"
            else:
                st.warning(f"Image {img_path} not found for node {node}")
        except Exception as e:
            st.error(f"Error loading image {node}.png: {str(e)}")
    return images

@st.cache_data
def load_graph_from_file(_file, file_format):
    try:
        file_content = _file.read()
        _file.seek(0)
        
        if file_format == "Edge List CSV":
            df = pd.read_csv(_file)
            G = nx.DiGraph()
            edges = df.values.tolist()
            # Add nodes first
            nodes = set()
            for edge in tqdm(edges, desc="Extracting nodes", leave=False):
                nodes.add(edge[0])
                nodes.add(edge[1])
            for node in tqdm(nodes, desc="Adding nodes", leave=False):
                G.add_node(node)
            # Add edges
            for edge in tqdm(edges, desc="Adding edges", leave=False):
                G.add_edge(edge[0], edge[1], weight=edge[2] if len(edge) > 2 else 1.0, 
                          label=edge[3] if len(edge) > 3 else '')
        elif file_format == "JSON":
            data = eval(file_content.decode("utf-8"))
            G = nx.DiGraph()
            for node in tqdm(data['nodes'], desc="Adding nodes", leave=False):
                G.add_node(node['id'])
            for edge in tqdm(data['links'], desc="Adding edges", leave=False):
                G.add_edge(
                    edge['source'], edge['target'],
                    weight=edge.get('weight', 1.0),
                    label=edge.get('label', '')
                )
        else:
            raise ValueError(f"Unsupported format: {file_format}")
        return G
    except Exception as e:
        st.error(f"Error loading graph: {str(e)}")
        return None

def get_prerequisite_subgraph(G, target_node, visited=None, subgraph=None):
    if visited is None:
        visited = set()
    if subgraph is None:
        subgraph = nx.DiGraph()
    
    subgraph.add_node(target_node)
    predecessors = list(G.predecessors(target_node))
    
    for pred in predecessors:
        # Copy edge attributes when adding edges
        edge_data = G.get_edge_data(pred, target_node)
        subgraph.add_edge(pred, target_node, **edge_data)
        
        if pred not in visited:
            visited.add(pred)
            get_prerequisite_subgraph(G, pred, visited, subgraph)
    
    return subgraph

def visualize_network(G, node_images):
    """Visualize the network using Plotly with node images, arrows, and edge labels."""
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Create edges with arrows and labels
    edge_traces = []
    for edge in tqdm(G.edges(data=True), desc="Creating edges", leave=False):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Calculate the edge vector
        dx = x1 - x0
        dy = y1 - y0
        length = (dx**2 + dy**2)**0.5
        
        if length != 0:
            # Normalize direction vector
            ux = dx / length
            uy = dy / length
            
            # Offset from nodes
            node_offset = 0.06
            x0_adjusted = x0 + (ux * node_offset)
            y0_adjusted = y0 + (uy * node_offset)
            x1_adjusted = x1 - (ux * node_offset)
            y1_adjusted = y1 - (uy * node_offset)
            
            # Arrow parameters
            arrow_length = 0.01
            arrow_width = 0.01
            
            # Calculate arrow head points
            # Point where arrow head starts
            arrow_base_x = x1_adjusted - (arrow_length * ux)
            arrow_base_y = y1_adjusted - (arrow_length * uy)
            
            # Calculate perpendicular vector for arrow head width
            perpx = -uy  # Perpendicular to (ux, uy)
            perpy = ux
            
            # Calculate the two points that form the arrow head
            arrow_left_x = arrow_base_x + (arrow_width * perpx)
            arrow_left_y = arrow_base_y + (arrow_width * perpy)
            arrow_right_x = arrow_base_x - (arrow_width * perpx)
            arrow_right_y = arrow_base_y - (arrow_width * perpy)
            
            # Create main edge line
            edge_trace = go.Scatter(
                x=[x0_adjusted, arrow_base_x],
                y=[y0_adjusted, arrow_base_y],
                line=dict(width=1.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces.append(edge_trace)
            
            # Create left side of arrow head
            arrow_left = go.Scatter(
                x=[arrow_left_x, x1_adjusted],
                y=[arrow_left_y, y1_adjusted],
                line=dict(width=1.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces.append(arrow_left)
            
            # Create right side of arrow head
            arrow_right = go.Scatter(
                x=[arrow_right_x, x1_adjusted],
                y=[arrow_right_y, y1_adjusted],
                line=dict(width=1.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces.append(arrow_right)
            
            # Add edge label if it exists
            if 'label' in edge[2] and edge[2]['label']:
                mid_x = (x0_adjusted + x1_adjusted) / 2
                mid_y = (y0_adjusted + y1_adjusted) / 2
                
                label_trace = go.Scatter(
                    x=[mid_x],
                    y=[mid_y],
                    text=[str(edge[2]['label'])],
                    mode='text',
                    textposition='middle center',
                    textfont=dict(size=10, color='#000'),
                    hoverinfo='none'
                )
                edge_traces.append(label_trace)

    # Create node traces
    node_x = []
    node_y = []
    node_images_traces = []
    node_text = []

    for node in tqdm(G.nodes(), desc="Creating nodes", leave=False):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}")

        if node in node_images:
            node_images_traces.append(
                dict(
                    source=node_images[node],
                    x=x,
                    y=y,
                    xref="x",
                    yref="y",
                    sizex=0.10,
                    sizey=0.10,
                    xanchor="center",
                    yanchor="middle",
                    layer="above"
                )
            )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        marker=dict(
            size=10,
            color='rgba(0,0,0,0)',
            line_width=2
        )
    )

    # Combine all traces
    fig = go.Figure(
        data=[*edge_traces, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    # Add node images as layout images
    for img_trace in tqdm(node_images_traces, desc="Adding image traces", leave=False):
        fig.add_layout_image(img_trace)

    return fig

# Main function remains the same
def main():
    st.title('Interactive Network Visualization with Node Images')

    file_format = st.selectbox("Select file format", ["JSON", "Edge List CSV"])
    uploaded_file = st.file_uploader("Upload graph file", type=["csv", "json"])

    if uploaded_file:
        G = load_graph_from_file(uploaded_file, file_format)
        
        if G:
            node_images = load_node_images(G.nodes())
            
            all_nodes = sorted(list(G.nodes()))
            selected_node = st.selectbox(
                "Select a node to view its prerequisites (type to search)",
                [""] + all_nodes,
                format_func=lambda x: "View full graph" if x == "" else x
            )
            
            st.write("### Network Metrics")
            col1, col2, col3 = st.columns(3)
            
            if selected_node:
                subgraph = get_prerequisite_subgraph(G, selected_node)
                with col1:
                    st.metric("Number of Prerequisites", subgraph.number_of_nodes() - 1)
                with col2:
                    st.metric("Number of Relationships", subgraph.number_of_edges())
                with col3:
                    st.metric("Depth", nx.dag_longest_path_length(subgraph) if nx.is_directed_acyclic_graph(subgraph) else "Contains cycles")
                
                fig = visualize_network(subgraph, node_images)
            else:
                with col1:
                    st.metric("Number of Nodes", G.number_of_nodes())
                with col2:
                    st.metric("Number of Edges", G.number_of_edges())
                with col3:
                    st.metric("Is DAG", "Yes" if nx.is_directed_acyclic_graph(G) else "No (Contains cycles)")
                
                fig = visualize_network(G, node_images)
            
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("View Graph Data"):
                if selected_node:
                    st.write("#### Selected Node:", selected_node)
                    st.write("#### Prerequisite Nodes:", list(subgraph.nodes()))
                    st.write("#### Prerequisite Relationships:", list(subgraph.edges(data=True)))
                else:
                    st.write("#### All Nodes:", list(G.nodes()))
                    st.write("#### All Edges:", list(G.edges(data=True)))

if __name__ == "__main__":
    main()