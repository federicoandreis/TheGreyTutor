import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

test_nodes = [
    # Artifacts
    ("Artifact", {"name": "Elven Sword", "aliases": ["Blade of the Elves"], "material": "Mithril", "current_status": "Lost"}),
    ("Artifact", {"name": "elven sword", "aliases": ["Elven Blade"], "material": "mithril", "current_status": "Found"}),
    # Characters
    ("Character", {"name": "Frodo Baggins", "aliases": ["Frodo", "Ringbearer"], "race": "Hobbit"}),
    ("Character", {"name": "frodo baggins", "aliases": ["Frodo", "Ring Bearer"], "race": "Hobbit", "title": "Mr."}),
    # Communities
    ("Community", {"name": "Rivendell", "description": "Elven refuge"}),
    ("Community", {"name": "rivendell", "description": "Hidden valley"}),
    # Events
    ("Event", {"name": "Battle of Five Armies", "aliases": ["The Great Battle"], "year": 2941}),
    ("Event", {"name": "battle of five armies", "aliases": ["Great Battle"], "year": 2941}),
    # Locations
    ("Location", {"name": "Mount Doom", "aliases": ["Orodruin"], "material": "Lava"}),
    ("Location", {"name": "mount doom", "aliases": ["orodruin"], "material": "lava"}),
    # Organizations
    ("Organization", {"name": "Fellowship of the Ring", "aliases": ["The Nine Walkers"]}),
    ("Organization", {"name": "fellowship of the ring", "aliases": ["Nine Walkers"]}),
]

def insert_test_duplicates():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        # First, create all nodes
        for label, props in test_nodes:
            prop_keys = ", ".join(f"{k}: ${k}" for k in props.keys())
            query = f"CREATE (n:`{label}` {{ {prop_keys} }})"
            session.run(query, **props)
        print("Test duplicate nodes inserted.")

        # Second, create relationships using loose name matching
        def get_node_id(label, name):
            # Fetch all candidates, match in Python (no APOC, no Cypher type errors)
            query = f"MATCH (n:`{label}`) RETURN elementId(n) AS eid, n.name AS name, n.aliases AS aliases"
            for record in session.run(query):
                n_name = record["name"]
                n_aliases = record.get("aliases", [])
                # Only match if name is a string
                if isinstance(n_name, str) and n_name.lower() == name.lower():
                    return record["eid"]
                # Only match if aliases is a list of strings
                if isinstance(n_aliases, list) and any(isinstance(a, str) and a.lower() == name.lower() for a in n_aliases):
                    return record["eid"]
            return None

        # (Optional) Warn about nodes with non-string names (for debugging)
        # query = "MATCH (n) RETURN labels(n) AS labels, n.name AS name, elementId(n) AS eid LIMIT 10"
        # for record in session.run(query):
        #     if not isinstance(record['name'], str):
        #         print(f"[WARNING] Node with non-string name: labels={record['labels']}, name={record['name']}, eid={record['eid']}")

        # Frodo Baggins MEMBER_OF Fellowship of the Ring
        frodo_id = get_node_id("Character", "Frodo Baggins") or get_node_id("Character", "frodo baggins")
        fellowship_id = get_node_id("Organization", "Fellowship of the Ring") or get_node_id("Organization", "fellowship of the ring")
        if frodo_id and fellowship_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:MEMBER_OF]->(b)", aid=frodo_id, bid=fellowship_id)

        # Frodo Baggins RESIDENT_OF Rivendell
        rivendell_id = get_node_id("Community", "Rivendell") or get_node_id("Community", "rivendell")
        if frodo_id and rivendell_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:RESIDENT_OF]->(b)", aid=frodo_id, bid=rivendell_id)

        # Elven Sword FOUND_AT Rivendell
        sword_id = get_node_id("Artifact", "Elven Sword") or get_node_id("Artifact", "elven sword")
        if sword_id and rivendell_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:FOUND_AT]->(b)", aid=sword_id, bid=rivendell_id)

        # Battle of Five Armies OCCURRED_AT Mount Doom
        battle_id = get_node_id("Event", "Battle of Five Armies") or get_node_id("Event", "battle of five armies")
        mount_doom_id = get_node_id("Location", "Mount Doom") or get_node_id("Location", "mount doom")
        if battle_id and mount_doom_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:OCCURRED_AT]->(b)", aid=battle_id, bid=mount_doom_id)

        # Fellowship of the Ring VISITED Mount Doom
        if fellowship_id and mount_doom_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:VISITED]->(b)", aid=fellowship_id, bid=mount_doom_id)

        # Bilbo Baggins FRIEND_OF Frodo Baggins (if Bilbo exists)
        bilbo_id = get_node_id("Character", "Bilbo Baggins") or get_node_id("Character", "bilbo baggins")
        if bilbo_id and frodo_id:
            session.run("MATCH (a),(b) WHERE elementId(a) = $aid AND elementId(b) = $bid CREATE (a)-[:FRIEND_OF]->(b)", aid=bilbo_id, bid=frodo_id)

    driver.close()
    print("Test relationships inserted.")

if __name__ == "__main__":
    insert_test_duplicates()
