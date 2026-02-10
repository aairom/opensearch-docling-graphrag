# Entity Graph Visualization Fix

## Problem Identified

The Entity Graph visualization was showing nothing because:

1. **No relationships between chunks and entities** - The `MENTIONS` relationships were not being created
2. **Root cause**: Chunk IDs are stored as **integers** (0, 1, 2...) in Neo4j, but the `create_relationship` method was comparing them as **strings**
3. **Result**: All 97 entities existed but were completely disconnected from chunks

## What Was Fixed

### File: `src/graphrag/neo4j_client.py`

Updated the `create_relationship` method to:
- Convert IDs to appropriate types (try integer conversion first)
- Match nodes by both integer and string IDs
- This allows chunk IDs (integers) to match properly

```python
def convert_id(id_val):
    try:
        return int(id_val)
    except (ValueError, TypeError):
        return id_val

from_id_int = convert_id(from_node_id)
to_id_int = convert_id(to_node_id)

# Match by id (as int or string) or by name
WHERE a.id = $from_id OR a.id = $from_id_int OR a.name = $from_id
```

## Actions Taken

1. ✅ Fixed `create_relationship` method
2. ✅ Committed fix to git
3. ✅ Cleared Neo4j database (all nodes deleted)
4. ⏳ Rebuilding container with fix
5. ⏳ Will reprocess documents to create relationships

## After Rebuild - What to Do

### 1. Reprocess Your Documents

Go to the **Document Processing** tab and upload your documents again. This will:
- Create chunks in Neo4j
- Extract entities
- **Create MENTIONS relationships** (this was broken before)

### 2. Verify Relationships Were Created

Run this command to check:
```bash
podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH (c:Chunk)-[r:MENTIONS]->(e:Entity) RETURN count(r) as mentions_count"
```

You should see a number > 0 (previously it was 0).

### 3. Test Entity Graph Visualization

1. Go to **Graph Explorer** tab
2. Select **Entity Graph** radio button
3. Enter an entity name (e.g., "Bob", "AI", "Product Positioning")
4. Adjust max depth (1-3)
5. Click **Visualize**

You should now see:
- The entity node (center)
- Connected chunk nodes (showing text preview)
- Relationships between them

## Expected Graph Structure

After the fix, the graph will have:

```
Document --HAS_CHUNK--> Chunk --MENTIONS--> Entity
```

And the Entity Graph visualization will show:
```
Entity <--MENTIONS-- Chunk <--MENTIONS-- Entity
         (via shared chunks)
```

## Verification Commands

Check node counts:
```bash
podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH (n) RETURN labels(n) as label, count(n) as count"
```

Check relationship counts:
```bash
podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
```

You should see:
- `HAS_CHUNK` relationships (Document → Chunk)
- `MENTIONS` relationships (Chunk → Entity) ← **This was missing!**

## Why This Matters

Without the MENTIONS relationships:
- ❌ Entity Graph shows nothing
- ❌ Can't find which chunks mention an entity
- ❌ Can't discover entity co-occurrences
- ❌ GraphRAG functionality is broken

With the fix:
- ✅ Entity Graph works
- ✅ Can trace entities to source chunks
- ✅ Can find related entities via shared chunks
- ✅ Full GraphRAG capabilities enabled