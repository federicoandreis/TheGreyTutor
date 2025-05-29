import os
import json
import openai
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to the deduplication groups file
GROUPS_FILE = "duplicate_groups_by_type.json"

# System prompt for the LLM
SYSTEM_PROMPT = (
    "You are a knowledge graph deduplication expert. "
    "You will be given a group of nodes that have been clustered as possible duplicates. "
    "For each group, decide if the nodes are true duplicates (should be merged) or not (should be kept separate). "
    "Use all available properties for your reasoning. "
    "Respond ONLY with 'MERGE' if you are confident they are duplicates, or 'KEEP SEPARATE' if not."
)

# Compose a prompt for a group
def compose_prompt(node_type, group_nodes):
    prompt = f"Node type: {node_type}\nNodes in group ({len(group_nodes)}):\n"
    for idx, node in enumerate(group_nodes, 1):
        prompt += f"Node {idx}:\n"
        for k, v in (node.items() if isinstance(node, dict) else enumerate(node)):
            prompt += f"  {k}: {v}\n"
    prompt += "\nDecision: "
    return prompt

# --- Pairwise LLM decision ---
def pairwise_llm_decision(node_type, node_a, node_b):
    prompt = (
        f"You are a knowledge graph deduplication expert and a master of Tolkien lore. "
        f"You will be given two nodes from a group of possible duplicates. "
        f"For each pair, decide if they are true duplicates (MERGE) or not (KEEP SEPARATE). "
        f"If merging, also propose the best name and how to merge their string/list properties. "
        f"Here are the two nodes (with all properties):\n"
        f"Node 1: {json.dumps(node_a, ensure_ascii=False)}\n"
        f"Node 2: {json.dumps(node_b, ensure_ascii=False)}\n"
        f"\nRespond ONLY with one of the following formats (no explanation):\n"
        f"MERGE; name=<best_name>; merged_properties=<merged_properties_JSON>\n"
        f"KEEP SEPARATE"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        max_tokens=256, temperature=0
    )
    answer = response.choices[0].message.content.strip()
    return answer

# --- Merge two nodes, using LLM's merge output ---
def merge_nodes(node_a, node_b, merge_response):
    # Example merge_response: 'MERGE; name=Orcs; merged_properties={...}'
    # Parse the merge_response
    import re
    name_match = re.search(r'name=(.*?);', merge_response)
    props_match = re.search(r'merged_properties=({.*})', merge_response)
    if name_match:
        best_name = name_match.group(1).strip()
    else:
        best_name = node_a.get('name', '')
    merged_props = node_a.copy()
    if props_match:
        try:
            merged_json = json.loads(props_match.group(1))
            merged_props.update(merged_json)
        except Exception:
            pass
    merged_props['name'] = best_name
    # Merge relationships if present
    rels_a = node_a.get('relationships', {})
    rels_b = node_b.get('relationships', {})
    merged_rels = {}
    for k in set(rels_a.keys()).union(rels_b.keys()):
        merged_rels[k] = rels_a.get(k, []) + rels_b.get(k, [])
    if merged_rels:
        merged_props['relationships'] = merged_rels
    return merged_props

# --- Sequential group deduplication ---
def sequential_group_deduplication(node_type, group_nodes, group_idx, store_results=None):
    # Track merges as a union-find structure
    n = len(group_nodes)
    parent = list(range(n))  # Initially, each node is its own parent
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    # Sequentially process merges
    i = 0
    while i < n - 1:
        a, b = find(i), find(i+1)
        if a == b:
            i += 1
            continue
        node_a = group_nodes[a]
        node_b = group_nodes[b]
        decision = pairwise_llm_decision(node_type, node_a, node_b)
        names = [n.get('name', '') for n in group_nodes]
        if decision.startswith('MERGE'):
            parent_b = find(b)
            parent[parent_b] = find(a)
            print(f"[{node_type}] Group {group_idx}: {names} Decision: MERGE")
            # After merge, stay at same index to check new group
        elif 'KEEP SEPARATE' in decision:
            print(f"[{node_type}] Group {group_idx}: {names} Decision: KEEP SEPARATE")
            i += 1
        else:
            print(f"[{node_type}] Group {group_idx}: {names} Decision: UNKNOWN")
            i += 1
    # Generate mapping list
    root_map = {}
    ids = [n.get('id', str(idx)) for idx, n in enumerate(group_nodes)]
    mapping = []
    idx_map = {}
    next_idx = 0
    for i in range(n):
        root = find(i)
        if root not in idx_map:
            idx_map[root] = i  # assign representative index
        mapping.append(idx_map[root])
    if store_results is not None:
        store_results.append({"nodes": ids, "merge": mapping})
    return ids, mapping


def main():
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        groups_by_type = json.load(f)
    merged_groups_by_type = {}
    for node_type, groups in groups_by_type.items():
        merged_groups = []
        for idx, group in enumerate(groups, 1):
            group_nodes = []
            for node_entry in group["nodes"]:
                if isinstance(node_entry, list):
                    node_dict = {}
                    if len(node_entry) > 2:
                        node_dict["id"] = node_entry[0]
                        node_dict["labels"] = node_entry[1]
                        node_dict["name"] = node_entry[2]
                        node_dict["aliases"] = node_entry[3] if len(node_entry) > 3 else []
                    else:
                        node_dict = {str(i): v for i, v in enumerate(node_entry)}
                    group_nodes.append(node_dict)
                elif isinstance(node_entry, dict):
                    group_nodes.append(node_entry)
            # Sequential pairwise deduplication, store results
            sequential_group_deduplication(node_type, group_nodes, idx, store_results=merged_groups)
        merged_groups_by_type[node_type] = merged_groups
    # Write merged groups to file
    with open("merged_groups_by_type.json", "w", encoding="utf-8") as f:
        json.dump(merged_groups_by_type, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
