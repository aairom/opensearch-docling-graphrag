# Graph Visualization Complete Guide

## 🎉 Overview

Interactive graph visualization has been added to the Graph Explorer using PyVis. This guide covers everything you need to know.

---

## 🔧 Bug Fix Applied

### The Problem
Entities had no connections in Neo4j because the `create_relationship` method was trying to match both nodes using the `id` property, but:
- **Chunks** use `id` property (e.g., "doc123_chunk_0")
- **Entities** use `name` property (e.g., "Bob", "Python")

### The Solution
Updated `src/graphrag/neo4j_client.py` to match nodes by either `id` OR `name`:
```python
MATCH (a) WHERE a.id = $from_id OR a.name = $from_id
MATCH (b) WHERE b.id = $to_id OR b.name = $to_id
MERGE (a)-[r:MENTIONS]->(b)
```

---

## 🚀 Quick Start

### After Container Rebuild

1. **Wait for rebuild to complete** (you'll see "✅ Application rebuilt and started successfully!")

2. **Open the application:** http://localhost:8501

3. **Process a NEW document:**
   - Go to "Upload" tab
   - Choose a PDF, DOCX, or other document
   - Click "Process Document"
   - Wait for completion

4. **Test visualization:**
   - Go to "Graph Explorer" → "Visualize" tab
   - Select "Entity Graph"
   - Enter an entity name from your document
   - Click "🎨 Visualize Entity"
   - **You should see an interactive graph!** 🎉

### Alternative: Start Fresh

If you want to clear all old data:
```bash
./stop.sh
podman volume rm opensearch-docling-graphrag_neo4j_data
./start.sh
# Then re-process all documents
```

---

## 📊 Features

### Three Visualization Types

#### 1. Entity Graph
- Focus on a specific entity
- Shows connections up to N levels deep
- Explore relationships between entities
- **Use case:** "Show me everything connected to 'Bob'"

#### 2. Document Structure
- Shows document → chunks → entities hierarchy
- Visualize how documents are organized
- See which entities are mentioned where
- **Use case:** "Show me the structure of this document"

#### 3. Full Graph
- Overview of entire knowledge base
- Adjustable node limit
- Good for understanding overall structure
- **Use case:** "Show me everything in the database"

### Interactive Features

Once the graph appears:
- **Click and drag** nodes to rearrange them
- **Scroll** to zoom in/out
- **Hover** over nodes to see details
- **Click** nodes to highlight connections
- **Physics simulation** creates natural layout

### Color Legend

- 🔵 **Blue Box** = Document
- 🟢 **Green Circle** = Chunk
- 🔴 **Red Star** = Entity
- 🟠 **Orange** = Person
- 🟣 **Purple** = Organization
- 🔷 **Teal** = Location

---

## 🔍 Using the UI

### Visualize Tab

**Entity Graph:**
1. Enter entity name (e.g., "Bob", "Python", "AI")
2. Set max depth (1-5 levels)
3. Click "🎨 Visualize Entity"

**Document Structure:**
1. Select document from dropdown (or "All Documents")
2. Click "🎨 Visualize Document"
3. See the hierarchy

**Full Graph:**
1. Adjust max nodes slider (10-200)
2. Click "🎨 Visualize Full Graph"
3. ⚠️ May be slow for large graphs

### Search Tab

1. Enter entity name to search
2. Click "Search"
3. Expand results to see connections
4. Click "Visualize [entity name]" for any result

### Statistics Tab

- View document, chunk, entity, and relationship counts
- See top 10 most connected entities
- Understand your knowledge graph structure

---

## ✅ Verification

### Check 1: MENTIONS Relationships Exist

```bash
podman exec docling-app python3 -c "
from src.graphrag import Neo4jClient
client = Neo4jClient()
with client.driver.session() as session:
    result = session.run('MATCH ()-[r:MENTIONS]->() RETURN count(r) as count')
    print(f'MENTIONS relationships: {result.single()[\"count\"]}')
"
```

**Expected:** Should show a number > 0 (e.g., 150, 200, etc.)

### Check 2: Entities Have Connections

```bash
podman exec docling-app python3 -c "
from src.graphrag import Neo4jClient
client = Neo4jClient()
with client.driver.session() as session:
    result = session.run('MATCH (e:Entity)-[r]-() RETURN count(DISTINCT e) as count')
    print(f'Entities with relationships: {result.single()[\"count\"]}')
"
```

**Expected:** Should show connected entities (not 0)

### Check 3: Visualization Works

1. Go to Graph Explorer → Visualize tab
2. Try visualizing an entity
3. You should see:
   - Entity node in center
   - Connected chunks around it
   - Possibly other related entities
   - Interactive graph you can manipulate

---

## 🐛 Troubleshooting

### "Graph is Empty" or "Nothing Happens"

**Cause:** No data or old data without relationships

**Solutions:**
1. **Process a NEW document** after the rebuild
2. **Check if MENTIONS relationships exist** (see Verification above)
3. **Clear old data and re-process:**
   ```bash
   ./stop.sh
   podman volume rm opensearch-docling-graphrag_neo4j_data
   ./start.sh
   ```

### "Entity Not Found"

**Cause:** Entity doesn't exist or typo

**Solutions:**
1. Use the **Search tab** to find entities
2. Check **Statistics tab** for top entities
3. Try a different entity name

### "Visualization Not Loading"

**Cause:** Browser issue or large graph

**Solutions:**
1. Check browser console for errors (F12)
2. Refresh the page
3. Reduce max_nodes parameter
4. Try a different browser

### "Container Won't Start"

**Solutions:**
1. Check logs: `podman logs docling-app`
2. Check if ports are in use: `lsof -i :8501`
3. Try: `./stop.sh && ./start.sh`

### "Can't Connect to Neo4j"

**Solutions:**
1. Check if Neo4j is running: `podman ps | grep neo4j`
2. Check Neo4j logs: `podman logs neo4j`
3. Try restarting: `podman restart neo4j`
4. Access Neo4j browser: http://localhost:7474 (login: neo4j/password)

---

## 🔬 Technical Details

### What Was Added

**New Files:**
- `src/graphrag/graph_visualizer.py` (349 lines) - PyVis visualization class
- `docs/GRAPH_VISUALIZATION_GUIDE.md` - This guide
- `docs/GRAPH_VISUALIZATION_INTEGRATION.md` - Developer integration guide
- `docs/GRAPH_VISUALIZATION_TROUBLESHOOTING.md` - Detailed troubleshooting

**Modified Files:**
- `src/graphrag/__init__.py` - Export GraphVisualizer
- `src/graphrag/neo4j_client.py` - Fixed create_relationship method
- `app.py` - Enhanced Graph Explorer tab with visualization
- `requirements.txt` - Added pyvis==0.3.2

### GraphVisualizer Class

```python
class GraphVisualizer:
    def visualize_entity_graph(entity_name, max_depth=2, max_nodes=50):
        """Create interactive graph centered on an entity"""
        
    def visualize_document_graph(document_id=None, max_nodes=100):
        """Create interactive graph showing document structure"""
        
    def render_graph(html):
        """Render graph in Streamlit"""
```

### Neo4j Query Changes

**Before (Broken):**
```cypher
MATCH (a {id: $from_id})
MATCH (b {id: $to_id})
MERGE (a)-[r:MENTIONS]->(b)
```

**After (Fixed):**
```cypher
MATCH (a) WHERE a.id = $from_id OR a.name = $from_id
MATCH (b) WHERE b.id = $to_id OR b.name = $to_id
MERGE (a)-[r:MENTIONS]->(b)
```

---

## 📚 Additional Resources

### Documentation
- **Integration Guide:** `docs/GRAPH_VISUALIZATION_INTEGRATION.md` - For developers
- **Troubleshooting:** `docs/GRAPH_VISUALIZATION_TROUBLESHOOTING.md` - Detailed debugging

### Neo4j Browser
- **URL:** http://localhost:7474
- **Login:** neo4j / password
- **Use for:** Direct Cypher queries, data inspection

### Useful Cypher Queries

**Count all nodes:**
```cypher
MATCH (n) RETURN labels(n) as type, count(*) as count
```

**Count all relationships:**
```cypher
MATCH ()-[r]->() RETURN type(r) as type, count(*) as count
```

**Find entities without connections:**
```cypher
MATCH (e:Entity) WHERE NOT (e)-[]-() RETURN e.name LIMIT 10
```

**Find most connected entities:**
```cypher
MATCH (e:Entity)-[r]-()
RETURN e.name, count(r) as connections
ORDER BY connections DESC
LIMIT 10
```

---

## 🎯 Best Practices

### For Best Results

1. **Process documents after the rebuild** - Old documents don't have MENTIONS relationships
2. **Start with Entity Graph** - Easier to understand than full graph
3. **Use Search tab first** - Find entities before visualizing
4. **Limit node count** - Large graphs can be slow
5. **Check Statistics** - Understand your data before visualizing

### Performance Tips

- **Entity Graph:** Use max_depth=2 for most cases
- **Document Structure:** Good for individual documents
- **Full Graph:** Use max_nodes=50 or less for large databases
- **Refresh page** if graph becomes unresponsive

---

## 🆘 Getting Help

### Check These First

1. **Application logs:** `podman logs -f docling-app`
2. **Neo4j browser:** http://localhost:7474
3. **Container status:** `podman ps`
4. **This guide:** You're reading it! 📖

### Common Issues Summary

| Issue | Quick Fix |
|-------|-----------|
| Empty graph | Process new document after rebuild |
| Entity not found | Use Search tab to find entities |
| Slow visualization | Reduce max_nodes parameter |
| Container won't start | `./stop.sh && ./start.sh` |
| Neo4j connection error | `podman restart neo4j` |

---

## Made with Bob 🤖

Enjoy exploring your knowledge graph with interactive visualizations! 🎨🕸️