#!/bin/bash

# Verify Neo4j Relationships After Fix
# This script checks if MENTIONS relationships were created successfully

echo "🔍 Checking Neo4j Database Status..."
echo ""

echo "📊 Node Counts:"
podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH (n) RETURN labels(n) as label, count(n) as count"
echo ""

echo "🔗 Relationship Counts:"
podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
echo ""

echo "✅ Checking MENTIONS Relationships (should be > 0):"
MENTIONS_COUNT=$(podman exec neo4j-docling cypher-shell -u neo4j -p password \
  "MATCH (c:Chunk)-[r:MENTIONS]->(e:Entity) RETURN count(r) as count" | tail -1 | tr -d '"')

if [ "$MENTIONS_COUNT" -gt 0 ]; then
  echo "✅ SUCCESS: Found $MENTIONS_COUNT MENTIONS relationships!"
  echo ""
  echo "📝 Sample relationships:"
  podman exec neo4j-docling cypher-shell -u neo4j -p password \
    "MATCH (c:Chunk)-[r:MENTIONS]->(e:Entity) RETURN c.id, e.name LIMIT 5"
else
  echo "❌ FAILED: No MENTIONS relationships found!"
  echo "   Please reprocess your documents through the UI."
fi

echo ""
echo "🎯 Entity Graph Visualization is now ready to use!"

# Made with Bob
