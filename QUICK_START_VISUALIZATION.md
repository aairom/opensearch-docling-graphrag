# Quick Start: Graph Visualization

## Step 1: Rebuild Complete ✓
The container is currently being rebuilt with the new visualization features.

## Step 2: Access the Application

Once the rebuild completes, you'll see output like:
```
✅ Application rebuilt and started successfully!
🌐 Access the application at: http://localhost:8501
```

Open that URL in your browser.

## Step 3: Navigate to Graph Explorer

1. In the sidebar, click **"Graph Explorer"**
2. You'll see three tabs:
   - **📊 Visualize** - Interactive graph visualization
   - **🔍 Search** - Search and visualize entities
   - **📈 Statistics** - Graph metrics and top entities

## Step 4: Try the Visualization

### Option A: Visualize an Entity
1. Go to **Visualize** tab
2. Select **"Entity Graph"**
3. Enter an entity name (e.g., "Bob", "Python", "AI")
4. Click **"🎨 Visualize Entity"**
5. You'll see an interactive network graph!

### Option B: Visualize Document Structure
1. Go to **Visualize** tab
2. Select **"Document Structure"**
3. Choose a document from the dropdown
4. Click **"🎨 Visualize Document"**
5. See how documents connect to chunks and entities

### Option C: Search and Visualize
1. Go to **Search** tab
2. Enter an entity name to search
3. Click **"Search"**
4. Expand any entity to see connections
5. Click **"Visualize [entity name]"** button

## Interactive Features

Once the graph appears:
- **Click and drag** nodes to rearrange them
- **Scroll** to zoom in/out
- **Hover** over nodes to see details
- **Click** nodes to highlight connections

## Color Legend

- 🔵 **Blue Box** = Document
- 🟢 **Green Circle** = Chunk
- 🔴 **Red Star** = Entity
- 🟠 **Orange** = Person
- 🟣 **Purple** = Organization
- 🔷 **Teal** = Location

## Troubleshooting

### Graph is Empty
- Make sure you've uploaded and processed documents first
- Go to **Upload** or **Batch Process** tab first
- Then return to Graph Explorer

### Can't Find Entity
- Try searching in the **Search** tab first
- Check **Statistics** tab to see what entities exist
- Entity names are case-insensitive

### Visualization Not Loading
- Refresh the page
- Check browser console for errors (F12)
- Try with fewer nodes (reduce max_nodes slider)

## What Changed

The **Graph Explorer** tab now has:
- ✅ Interactive PyVis visualizations
- ✅ Three visualization types (Entity/Document/Full)
- ✅ Entity search with inline visualization
- ✅ Enhanced statistics with top entities
- ✅ Color-coded nodes by type
- ✅ Drag, zoom, and hover interactions

Enjoy exploring your knowledge graph! 🎨🕸️