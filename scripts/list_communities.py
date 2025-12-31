"""
Script to list all available communities in the knowledge graph.
"""
from kg_quizzing.scripts.quiz_utils import get_available_communities

def main():
    communities = get_available_communities()
    print(f"Found {len(communities)} communities:")
    for i, community in enumerate(communities):
        print(f"{i+1}. ID: {community.get('id')}, Name: {community.get('name')}")

if __name__ == "__main__":
    main()
