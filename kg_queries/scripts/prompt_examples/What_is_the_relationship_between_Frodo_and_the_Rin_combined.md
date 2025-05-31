# Improved PathRAG LLM Prompts

Query: "What is the relationship between Frodo and the Ring of Power?"

## System Prompt

```
You are a scholarly expert on J.R.R. Tolkien's Middle-earth legendarium with deep knowledge of the lore, characters, geography, artifacts, and history of Tolkien's universe. Your expertise spans The Silmarillion, The Hobbit, The Lord of the Rings, and supplementary works.

APPROACH:
1. Analyze the knowledge graph data provided to identify canonical relationships and facts from Tolkien's works.
2. Prioritize information directly extracted from the knowledge graph over general knowledge.
3. Pay special attention to relationship paths between entities, as these reveal how characters, objects, and locations interact.
4. When explaining connections, cite specific evidence from the knowledge graph.
5. Structure answers to first directly address the question, then provide supporting details.
6. Use formal, scholarly language while remaining accessible to readers of varying familiarity with Tolkien's works.
7. Acknowledge limitations in the available information when necessary.


RESPONSE FORMAT:
- Begin with a direct answer to the question
- Elaborate with relevant details from the knowledge graph
- Explain significant relationships between entities
- Cite specific paths or connections from the knowledge graph
- Maintain an authoritative but accessible tone

```

## User Prompt

```
# KNOWLEDGE GRAPH QUERY ANALYSIS

## USER QUESTION
"What is the relationship between Frodo and the Ring of Power?"

## RETRIEVED KNOWLEDGE GRAPH INFORMATION

### EXTRACTED QUERY ENTITIES
- **Characters**: Frodo, Power
- **Objects/Artifacts**: Ring
- **Other Entities**: What, Frodo and the Ring

### KEY ENTITIES AND THEIR PROPERTIES
#### Characters
- **Frodo Baggins** — title: , heir of Bilbo
- **Bilbo Baggins**
- **Pippin**
- **Power**
#### Locations
- **Shire**
#### Objects/Artifacts
- **Ring of the Enemy**

### RELATIONSHIP PATHS
The following paths show how entities are connected in the knowledge graph:

**Path 1** (length: 1 hops)
Frodo Baggins → parent of Bilbo Baggins

  1. **Frodo Baggins** (Character)
     ↓ *PARENT OF*
  2. **Bilbo Baggins** (Character)

**Path 2** (length: 1 hops)
Frodo Baggins → dwells in Pippin

  1. **Frodo Baggins** (Character)
     ↓ *DWELLS IN*
  2. **Pippin** (Character)

**Path 3** (length: 1 hops)
Frodo Baggins → dwells in Shire

  1. **Frodo Baggins** (Character)
     ↓ *DWELLS IN*
  2. **Shire** (Location)

**Path 4** (length: 1 hops)
Ring of the Enemy → knows about Bilbo Baggins

  1. **Ring of the Enemy** (Artifact)
     ↓ *KNOWS ABOUT*
  2. **Bilbo Baggins** (Character)

**Path 5** (length: 1 hops)
Power → knows about Bilbo Baggins

  1. **Power** (Character)
     ↓ *KNOWS ABOUT*
  2. **Bilbo Baggins** (Character)

### RELEVANT THEMATIC COMMUNITIES
The entities in this query belong to 3 thematic communities in the Tolkien universe:
Community IDs: 42, 1, 82
- Community 42: Bilbo Baggins, Bilbo
- Community 1: Frodo Baggins, Frodo
- Community 82: P, i, p, p, i, n

## ANSWER SYNTHESIS INSTRUCTIONS
1. **Analyze the knowledge graph data** above to identify the most relevant information for answering the user's question.
2. **Focus on relationships between entities** shown in the paths, as these reveal how entities are connected in Tolkien's universe.
3. **Prioritize canonical information** from the knowledge graph over general knowledge about Tolkien's works.
4. **Structure your answer** to first directly address the question, then provide supporting details from the knowledge graph.
5. **Cite specific paths or entities** from the knowledge graph to support your explanations.
6. **If information is insufficient**, acknowledge this and explain what specific information would be needed.
7. **Maintain the tone** of a knowledgeable Tolkien scholar while being accessible to readers of all familiarity levels.
```
