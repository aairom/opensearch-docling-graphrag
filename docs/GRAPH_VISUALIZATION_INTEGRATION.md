# Graph Visualization Integration Guide

## Overview

This guide shows how to integrate PyVis graph visualization into the Streamlit app's Graph Explorer tab.

## What Was Added

### 1. New Dependency
- **pyvis==0.3.2** added to requirements.txt
- Interactive network graph visualization library

### 2. New Module
- **src/graphrag/graph_visualizer.py** (349 lines)
- GraphVisualizer class for creating interactive graphs
- Two main visualization methods:
  - `visualize_entity_graph()` - Show entity and connections
  - `visualize_document_graph()` - Show document structure

## Integration Steps

### Step 1: Update app.py Imports

Add to the imports section:

```python
from src.graphrag import Neo4jClient, GraphBuilder, GraphVisualizer
```

### Step 2: Initialize Visualizer in Session State

Add to session state initialization:

```python
if 'graph_visualizer' not in st.session_state:
    st.session_state.graph_visualizer = None
```

### Step 3: Initialize in initialize_clients()

Add to the `initialize_clients()` function:

```python
def initialize_clients():
    """Initialize all clients."""
    try:
        with st.spinner("Initializing clients..."):
            if not st.session_state.initialized:
                # ... existing initialization ...
                
                st.session_state.neo4j_client = Neo4jClient()
                st.session_state.graph_builder = GraphBuilder(st.session_state.neo4j_client)
                
                # Add graph visualizer
                st.session_state.graph_visualizer = GraphVisualizer(st.session_state.neo4j_client)
                
                st.session_state.initialized = True
                st.success("✅ All clients initialized successfully!")
                
    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
```

### Step 4: Update Graph Explorer Tab

Replace the existing `graph_explorer_tab()` function with this enhanced version:

```python
def graph_explorer_tab():
    st.header("🕸️ Knowledge Graph Explorer")
    
    # Tabs for different views
    viz_tab, search_tab, stats_tab = st.tabs(["📊 Visualize", "🔍 Search", "📈 Statistics"])
    
    with viz_tab:
        st.subheader("Interactive Graph Visualization")
        
        # Visualization options
        viz_type = st.radio(
            "Select visualization type:",
            ["Entity Graph", "Document Structure", "Full Graph"],
            horizontal=True
        )
        
        if viz_type == "Entity Graph":
            st.markdown("**Visualize an entity and its connections**")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                entity_name = st.text_input(
                    "Enter entity name:",
                    placeholder="e.g., Bob, Python, AI"
                )
            with col2:
                max_depth = st.number_input("Max depth:", min_value=1, max_value=5, value=2)
            
            if st.button("🎨 Visualize Entity", type="primary"):
                if entity_name:
                    try:
                        with st.spinner(f"Generating graph for '{entity_name}'..."):
                            html = st.session_state.graph_visualizer.visualize_entity_graph(
                                entity_name=entity_name,
                                max_depth=max_depth,
                                max_nodes=50
                            )
                            st.session_state.graph_visualizer.render_graph(html)
                            
                            st.success(f"✅ Graph generated for '{entity_name}'")
                            st.info("💡 **Tip:** Click and drag nodes, scroll to zoom, hover for details")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info("💡 Try searching for a different entity or check if documents have been processed")
                else:
                    st.warning("⚠️ Please enter an entity name")
        
        elif viz_type == "Document Structure":
            st.markdown("**Visualize document structure with chunks and entities**")
            
            # Get list of documents
            try:
                with st.session_state.neo4j_client.driver.session() as session:
                    result = session.run("MATCH (d:Document) RETURN d.id as id, d.file_name as name")
                    documents = [(r['id'], r['name']) for r in result]
                
                if documents:
                    doc_options = ["All Documents"] + [f"{name} ({id[:8]}...)" for id, name in documents]
                    selected = st.selectbox("Select document:", doc_options)
                    
                    if st.button("🎨 Visualize Document", type="primary"):
                        try:
                            with st.spinner("Generating document graph..."):
                                if selected == "All Documents":
                                    html = st.session_state.graph_visualizer.visualize_document_graph(
                                        document_id=None,
                                        max_nodes=100
                                    )
                                else:
                                    # Extract document ID from selection
                                    doc_id = [id for id, name in documents if name in selected][0]
                                    html = st.session_state.graph_visualizer.visualize_document_graph(
                                        document_id=doc_id,
                                        max_nodes=100
                                    )
                                
                                st.session_state.graph_visualizer.render_graph(html)
                                st.success("✅ Document graph generated")
                                
                                # Legend
                                st.markdown("---")
                                st.markdown("**Legend:**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("🔵 **Blue Box** = Document")
                                with col2:
                                    st.markdown("🟢 **Green Dot** = Chunk")
                                with col3:
                                    st.markdown("🔴 **Red Star** = Entity")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.info("📄 No documents found. Upload and process documents first.")
                    
            except Exception as e:
                st.error(f"❌ Error fetching documents: {str(e)}")
        
        else:  # Full Graph
            st.markdown("**Visualize the entire knowledge graph**")
            st.warning("⚠️ This may be slow for large graphs")
            
            max_nodes = st.slider("Maximum nodes to display:", 10, 200, 50)
            
            if st.button("🎨 Visualize Full Graph", type="primary"):
                try:
                    with st.spinner("Generating full graph..."):
                        html = st.session_state.graph_visualizer.visualize_document_graph(
                            document_id=None,
                            max_nodes=max_nodes
                        )
                        st.session_state.graph_visualizer.render_graph(html)
                        st.success("✅ Full graph generated")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with search_tab:
        st.subheader("🔍 Search Entities")
        
        entity_name = st.text_input("Search for entity:", key="search_entity")
        
        if st.button("Search", key="search_btn"):
            if entity_name:
                try:
                    # Search for entity
                    with st.session_state.neo4j_client.driver.session() as session:
                        result = session.run("""
                            MATCH (e:Entity)
                            WHERE toLower(e.name) CONTAINS toLower($name)
                            RETURN e.name as name, id(e) as id
                            LIMIT 20
                        """, name=entity_name)
                        
                        entities = list(result)
                        
                        if entities:
                            st.success(f"Found {len(entities)} entities:")
                            
                            for entity in entities:
                                with st.expander(f"🔴 {entity['name']}"):
                                    # Get connections
                                    conn_result = session.run("""
                                        MATCH (e:Entity)-[r]-(n)
                                        WHERE id(e) = $id
                                        RETURN type(r) as rel_type, labels(n) as labels, count(*) as count
                                    """, id=entity['id'])
                                    
                                    connections = list(conn_result)
                                    
                                    if connections:
                                        st.markdown("**Connections:**")
                                        for conn in connections:
                                            st.text(f"  • {conn['rel_type']} → {conn['labels'][0]}: {conn['count']}")
                                    
                                    # Visualize button
                                    if st.button(f"Visualize {entity['name']}", key=f"viz_{entity['id']}"):
                                        html = st.session_state.graph_visualizer.visualize_entity_graph(
                                            entity_name=entity['name'],
                                            max_depth=2
                                        )
                                        st.session_state.graph_visualizer.render_graph(html)
                        else:
                            st.info(f"No entities found matching '{entity_name}'")
                            
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter an entity name")
    
    with stats_tab:
        st.subheader("📈 Graph Statistics")
        
        try:
            with st.session_state.neo4j_client.driver.session() as session:
                # Get counts
                stats = {}
                
                # Document count
                result = session.run("MATCH (d:Document) RETURN count(d) as count")
                stats['documents'] = result.single()['count']
                
                # Chunk count
                result = session.run("MATCH (c:Chunk) RETURN count(c) as count")
                stats['chunks'] = result.single()['count']
                
                # Entity count
                result = session.run("MATCH (e:Entity) RETURN count(e) as count")
                stats['entities'] = result.single()['count']
                
                # Relationship count
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                stats['relationships'] = result.single()['count']
                
                # Display stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Documents", stats['documents'])
                with col2:
                    st.metric("Chunks", stats['chunks'])
                with col3:
                    st.metric("Entities", stats['entities'])
                with col4:
                    st.metric("Relationships", stats['relationships'])
                
                st.markdown("---")
                
                # Top entities
                st.markdown("**Top 10 Most Connected Entities:**")
                result = session.run("""
                    MATCH (e:Entity)-[r]-()
                    RETURN e.name as name, count(r) as connections
                    ORDER BY connections DESC
                    LIMIT 10
                """)
                
                top_entities = list(result)
                if top_entities:
                    for i, entity in enumerate(top_entities, 1):
                        st.text(f"{i}. {entity['name']}: {entity['connections']} connections")
                else:
                    st.info("No entities found")
                    
        except Exception as e:
            st.error(f"❌ Error fetching statistics: {str(e)}")
```

## Features

### Interactive Visualization
- **Click and drag** nodes to rearrange
- **Scroll** to zoom in/out
- **Hover** over nodes for details
- **Physics simulation** for natural layout
- **Color-coded** nodes by type

### Node Colors
- 🔵 **Blue** - Documents
- 🟢 **Green** - Chunks
- 🔴 **Red** - Entities
- 🟠 **Orange** - Persons
- 🟣 **Purple** - Organizations
- 🔷 **Teal** - Locations

### Three Visualization Types

1. **Entity Graph**
   - Focus on specific entity
   - Show connections up to N levels deep
   - Explore relationships

2. **Document Structure**
   - Show document → chunks → entities
   - Visualize document organization
   - See entity mentions

3. **Full Graph**
   - Overview of entire knowledge base
   - Adjustable node limit
   - Good for understanding overall structure

## Testing

### After Integration

1. **Rebuild container:**
   ```bash
   ./rebuild-app.sh
   ```

2. **Upload documents** through the UI

3. **Go to Graph Explorer tab**

4. **Try visualizations:**
   - Search for "Bob" in Entity Graph
   - View Document Structure
   - Check Statistics

## Troubleshooting

### Graph is Empty
- Check if documents were processed
- Verify Neo4j has data: `http://localhost:7474`
- Check logs for errors

### Visualization Not Loading
- Check browser console for errors
- Verify pyvis is installed: `pip list | grep pyvis`
- Try refreshing the page

### Performance Issues
- Reduce max_nodes parameter
- Limit max_depth for entity graphs
- Process fewer documents at once

## Made with Bob