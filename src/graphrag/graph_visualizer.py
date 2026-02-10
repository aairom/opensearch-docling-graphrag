"""
Graph visualization using PyVis for interactive network graphs.
"""
from typing import Dict, Any, List, Optional
from pyvis.network import Network
import streamlit.components.v1 as components
from loguru import logger
import tempfile
from pathlib import Path


class GraphVisualizer:
    """Visualize Neo4j graphs using PyVis."""
    
    def __init__(self, neo4j_client):
        """
        Initialize graph visualizer.
        
        Args:
            neo4j_client: Neo4j client instance
        """
        self.neo4j_client = neo4j_client
        logger.info("Graph visualizer initialized")
    
    def visualize_entity_graph(
        self,
        entity_name: str,
        max_depth: int = 2,
        max_nodes: int = 50
    ) -> str:
        """
        Create interactive visualization of entity and its connections.
        
        Args:
            entity_name: Name of entity to visualize
            max_depth: Maximum relationship depth
            max_nodes: Maximum number of nodes to display
            
        Returns:
            HTML string for visualization
        """
        try:
            # Create network
            net = Network(
                height="600px",
                width="100%",
                bgcolor="#222222",
                font_color="white",
                directed=True
            )
            
            # Configure physics
            net.set_options("""
            {
                "physics": {
                    "enabled": true,
                    "barnesHut": {
                        "gravitationalConstant": -30000,
                        "centralGravity": 0.3,
                        "springLength": 200,
                        "springConstant": 0.04
                    }
                },
                "nodes": {
                    "font": {
                        "size": 16,
                        "color": "white"
                    }
                },
                "edges": {
                    "font": {
                        "size": 12,
                        "color": "white",
                        "align": "middle"
                    },
                    "arrows": {
                        "to": {
                            "enabled": true,
                            "scaleFactor": 0.5
                        }
                    },
                    "smooth": {
                        "type": "continuous"
                    }
                }
            }
            """)
            
            # Get entity connections from Neo4j
            query = """
            MATCH path = (e:Entity {name: $entity_name})-[r*1..%d]-(n)
            RETURN path
            LIMIT $max_nodes
            """ % max_depth
            
            with self.neo4j_client.driver.session() as session:
                result = session.run(
                    query,
                    entity_name=entity_name,
                    max_nodes=max_nodes
                )
                
                nodes_added = set()
                edges_added = set()
                
                for record in result:
                    path = record['path']
                    
                    # Process nodes in path
                    for node in path.nodes:
                        node_id = str(node.id)
                        if node_id not in nodes_added:
                            # Determine node properties
                            labels = list(node.labels)
                            label = labels[0] if labels else "Node"
                            
                            # Set color based on label
                            color = self._get_node_color(label)
                            size = self._get_node_size(label)
                            
                            # Get node title (hover text)
                            title = self._get_node_title(node, label)
                            
                            # Get node label
                            node_label = self._get_node_label(node, label)
                            
                            # Add node
                            net.add_node(
                                node_id,
                                label=node_label,
                                title=title,
                                color=color,
                                size=size,
                                shape="dot"
                            )
                            nodes_added.add(node_id)
                    
                    # Process relationships in path
                    for rel in path.relationships:
                        edge_id = f"{rel.start_node.id}-{rel.end_node.id}"
                        if edge_id not in edges_added:
                            net.add_edge(
                                str(rel.start_node.id),
                                str(rel.end_node.id),
                                title=rel.type,
                                label=rel.type
                            )
                            edges_added.add(edge_id)
            
            # Generate HTML
            html = net.generate_html()
            
            logger.info(f"Generated graph visualization for '{entity_name}' with {len(nodes_added)} nodes")
            return html
            
        except Exception as e:
            logger.error(f"Error visualizing entity graph: {str(e)}")
            raise
    
    def visualize_document_graph(
        self,
        document_id: Optional[str] = None,
        max_nodes: int = 100
    ) -> str:
        """
        Visualize document structure and entities.
        
        Args:
            document_id: Specific document ID (None for all documents)
            max_nodes: Maximum number of nodes
            
        Returns:
            HTML string for visualization
        """
        try:
            net = Network(
                height="700px",
                width="100%",
                bgcolor="#222222",
                font_color="white",
                directed=True
            )
            
            # Configure physics
            net.set_options("""
            {
                "physics": {
                    "enabled": true,
                    "barnesHut": {
                        "gravitationalConstant": -50000,
                        "centralGravity": 0.5,
                        "springLength": 150
                    }
                }
            }
            """)
            
            # Query for document structure
            if document_id:
                query = """
                MATCH (d:Document {id: $document_id})
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
                RETURN d, c, e
                LIMIT $max_nodes
                """
                params = {'document_id': document_id, 'max_nodes': max_nodes}
            else:
                query = """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
                RETURN d, c, e
                LIMIT $max_nodes
                """
                params = {'max_nodes': max_nodes}
            
            with self.neo4j_client.driver.session() as session:
                result = session.run(query, **params)
                
                nodes_added = set()
                
                for record in result:
                    # Add document node
                    if record['d'] and str(record['d'].id) not in nodes_added:
                        doc = record['d']
                        net.add_node(
                            str(doc.id),
                            label=doc.get('file_name', 'Document'),
                            title=f"Document: {doc.get('file_name', 'Unknown')}",
                            color="#3498db",
                            size=30,
                            shape="box"
                        )
                        nodes_added.add(str(doc.id))
                    
                    # Add chunk node
                    if record['c'] and str(record['c'].id) not in nodes_added:
                        chunk = record['c']
                        # Get chunk label (text preview)
                        chunk_label = self._get_node_label(chunk, "Chunk")
                        net.add_node(
                            str(chunk.id),
                            label=chunk_label,
                            title=chunk.get('text', '')[:200] + "...",
                            color="#2ecc71",
                            size=15,
                            shape="dot"
                        )
                        nodes_added.add(str(chunk.id))
                        
                        # Add edge from document to chunk
                        if record['d']:
                            net.add_edge(
                                str(record['d'].id),
                                str(chunk.id),
                                title="HAS_CHUNK",
                                label="HAS_CHUNK"
                            )
                    
                    # Add entity node
                    if record['e'] and str(record['e'].id) not in nodes_added:
                        entity = record['e']
                        net.add_node(
                            str(entity.id),
                            label=entity.get('name', 'Entity'),
                            title=f"Entity: {entity.get('name', 'Unknown')}",
                            color="#e74c3c",
                            size=20,
                            shape="star"
                        )
                        nodes_added.add(str(entity.id))
                        
                        # Add edge from chunk to entity
                        if record['c']:
                            net.add_edge(
                                str(record['c'].id),
                                str(entity.id),
                                title="MENTIONS",
                                label="MENTIONS"
                            )
            
            html = net.generate_html()
            logger.info(f"Generated document graph with {len(nodes_added)} nodes")
            return html
            
        except Exception as e:
            logger.error(f"Error visualizing document graph: {str(e)}")
            raise
    
    def _get_node_color(self, label: str) -> str:
        """Get color for node based on label."""
        colors = {
            'Document': '#3498db',  # Blue
            'Chunk': '#2ecc71',     # Green
            'Entity': '#e74c3c',    # Red
            'Person': '#f39c12',    # Orange
            'Organization': '#9b59b6',  # Purple
            'Location': '#1abc9c',  # Teal
        }
        return colors.get(label, '#95a5a6')  # Gray default
    
    def _get_node_size(self, label: str) -> int:
        """Get size for node based on label."""
        sizes = {
            'Document': 30,
            'Chunk': 15,
            'Entity': 20,
            'Person': 25,
            'Organization': 25,
            'Location': 20,
        }
        return sizes.get(label, 15)
    
    def _get_node_title(self, node, label: str) -> str:
        """Get hover title for node."""
        props = dict(node)
        title_parts = [f"<b>{label}</b>"]
        
        # Add relevant properties
        if 'name' in props:
            title_parts.append(f"Name: {props['name']}")
        if 'file_name' in props:
            title_parts.append(f"File: {props['file_name']}")
        if 'text' in props:
            text = props['text'][:100] + "..." if len(props['text']) > 100 else props['text']
            title_parts.append(f"Text: {text}")
        
        return "<br>".join(title_parts)
    
    def _get_node_label(self, node, label: str) -> str:
        """
        Get appropriate label for a node.
        
        Args:
            node: Neo4j node
            label: Node label/type
            
        Returns:
            Label string for display
        """
        # For entities, use name
        if label == "Entity" or "Entity" in str(node.labels):
            return node.get('name', f"Entity_{node.id}")
        
        # For documents, use file_name
        if label == "Document":
            return node.get('file_name', f"Document_{node.id}")
        
        # For chunks, show preview of text
        if label == "Chunk":
            text = node.get('text', '')
            if text:
                # Get first 50 characters, clean up
                preview = text.strip()[:50]
                # Remove newlines and extra spaces
                preview = ' '.join(preview.split())
                # Add ellipsis if truncated
                if len(text) > 50:
                    preview += "..."
                return preview
            else:
                chunk_id = node.get('id', node.id)
                return f"Chunk {chunk_id}"
        
        # Default: use name, file_name, or label with ID
        return node.get('name', node.get('file_name', f"{label}_{node.id}"))
    
    def render_graph(self, html: str):
        """
        Render graph HTML in Streamlit.
        
        Args:
            html: HTML string from PyVis
        """
        components.html(html, height=650, scrolling=True)


# Made with Bob