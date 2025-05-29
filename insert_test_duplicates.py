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
        for label, props in test_nodes:
            prop_keys = ", ".join(f"{k}: ${k}" for k in props.keys())
            query = f"CREATE (n:`{label}` {{ {prop_keys} }})"
            session.run(query, **props)
    driver.close()
    print("Test duplicate nodes inserted.")

if __name__ == "__main__":
    insert_test_duplicates()
