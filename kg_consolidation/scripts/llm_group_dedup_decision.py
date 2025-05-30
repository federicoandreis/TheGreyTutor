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
    "You are an expert in Tolkien lore and advanced knowledge graph curation. "
    "Your task is to deduplicate nodes representing Tolkien universe entities (characters, artifacts, places, events, etc). "
    "You must pay special attention to aliases, names, and subtle variations in properties. "
    "When deciding if nodes are duplicates, consider canonical Tolkien facts and context, including variant spellings, titles, and relationships. "
    "Aliases and alternate names are crucial for matching. "
    "Err on the side of precision: only MERGE if you are confident all nodes refer to the same canonical entity. "
    "Respond ONLY with 'MERGE' if all nodes are true duplicates, or 'KEEP SEPARATE' if not. Do not explain your answer."
)

# Compose a prompt for a group
def compose_prompt(node_type, group_nodes):
    prompt = (
        f"You are a Tolkien knowledge graph deduplication expert.\n"
        f"Entity type: {node_type}\n"
        f"Below is a group of {len(group_nodes)} nodes clustered as possible duplicates.\n"
        f"For each group, decide if ALL nodes refer to the same canonical Tolkien entity.\n"
        f"Pay special attention to aliases, alternate spellings, and relationships.\n"
        f"List all node properties for reference.\n"
    )
    for idx, node in enumerate(group_nodes, 1):
        prompt += f"\nNode {idx}:\n"
        for k, v in (node.items() if isinstance(node, dict) else enumerate(node)):
            prompt += f"  {k}: {v}\n"
    prompt += (
        "\nRespond ONLY with one of the following (no explanation):\n"
        "MERGE\n"
        "KEEP SEPARATE\n"
        "\nDecision: "
    )
    return prompt

# --- Pairwise LLM decision ---
def pairwise_llm_decision(node_type, node_a, node_b):
    prompt = (
        f"You are a Tolkien knowledge graph deduplication expert.\n"
        f"You will be given two nodes of type '{node_type}' that may be duplicates.\n"
        f"Decide if they refer to the same canonical entity from Tolkien's legendarium.\n"
        f"Pay special attention to names, aliases, titles, and relationships.\n"
        f"If MERGE, propose the best canonical name and a merged property set.\n"
        f"Here are the two nodes (all properties shown):\n"
        f"Node 1: {json.dumps(node_a, ensure_ascii=False)}\n"
        f"Node 2: {json.dumps(node_b, ensure_ascii=False)}\n"
        f"\nRespond ONLY with one of the following (no explanation):\n"
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
    n = len(group_nodes)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    i = 0
    while i < n - 1:
        a, b = find(i), find(i+1)
        if a == b:
            i += 1
            continue
        node_a = group_nodes[a]
        node_b = group_nodes[b]
        response = pairwise_llm_decision(node_type, node_a, node_b)
        if response.startswith("MERGE"):
            merged_node = merge_nodes(node_a, node_b, response)
            group_nodes[a] = merged_node
            parent[b] = a
            if store_results:
                store_results.append({"group": group_idx, "merge": True, "a": node_a, "b": node_b, "merged": merged_node, "response": response})
        else:
            if store_results:
                store_results.append({"group": group_idx, "merge": False, "a": node_a, "b": node_b, "response": response})
        i += 1
    # Build ids and mapping
    ids = [n.get('id', str(idx)) for idx, n in enumerate(group_nodes)]
    idx_map = {}
    mapping = []
    for i in range(n):
        root = find(i)
        if root not in idx_map:
            idx_map[root] = i  # assign representative index
        mapping.append(idx_map[root])
    return ids, mapping


# --- Main execution ---
import sys

def mock_pairwise_llm_decision(node_type, node_a, node_b):
    # Always KEEP SEPARATE for testing; you can customize logic here
    return "KEEP SEPARATE"

def mock_sequential_group_deduplication(node_type, group_nodes, group_idx, store_results=None):
    # Just return the input group as-is (no merges)
    if store_results is not None:
        for i in range(len(group_nodes)-1):
            store_results.append({"group": group_idx, "merge": False, "a": group_nodes[i], "b": group_nodes[i+1], "response": "MOCK"})
    return group_nodes

def main():
    import argparse
    parser = argparse.ArgumentParser(description="LLM Group Deduplication")
    parser.add_argument('--mock', action='store_true', help='Run with mock LLM calls and print duplicate groups only')
    args = parser.parse_args()

    if not os.path.exists(GROUPS_FILE):
        print(f"Groups file not found: {GROUPS_FILE}")
        return
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        groups_by_type = json.load(f)
    results = []
    merged_groups_by_type = {}
    def node_list_to_dict(node):
        if isinstance(node, dict):
            return node
        if isinstance(node, list):
            keys = ["id", "labels", "name", "aliases"]
            return dict(zip(keys, node))
        return node

    for node_type, groups in groups_by_type.items():
        merged_groups = []
        for idx, group in enumerate(groups, 1):
            nodes = group['nodes'] if isinstance(group, dict) and 'nodes' in group else group
            nodes = [node_list_to_dict(n) for n in nodes]
            print(f"[{node_type}] Group {idx}: {[n['name'] if isinstance(n, dict) and 'name' in n else n for n in nodes]}", end=" ")
            if args.mock:
                # In mock mode, simulate merge mapping: each node is its own group
                node_ids = [n.get('id', str(i)) for i, n in enumerate(nodes)]
                mapping = list(range(len(nodes)))
                merged_groups.append({"nodes": node_ids, "merge": mapping})
                merged_group = mock_sequential_group_deduplication(node_type, nodes, idx, store_results=results)
                print("[MOCK MODE] Potential duplicates:", [n['name'] if isinstance(n, dict) and 'name' in n else n for n in nodes])
                # Add group-level summary to results
                decision = "MERGE" if len(set(mapping)) == 1 else "KEEP SEPARATE"
                results.append({
                    "node_type": node_type,
                    "group_number": idx,
                    "decision": decision,
                    "input_nodes": nodes,
                    "ids": node_ids,
                    "mapping": mapping
                })
            else:
                # sequential_group_deduplication returns (ids, mapping)
                ids, mapping = sequential_group_deduplication(node_type, nodes, idx, store_results=results)
                merged_groups.append({"nodes": ids, "merge": mapping})
                merged_group = [nodes[m] for m in set(mapping)]
                if len(merged_group) == 1:
                    print("Decision: MERGE")
                else:
                    print("Decision: KEEP SEPARATE")
                # Add group-level summary to results
                decision = "MERGE" if len(set(mapping)) == 1 else "KEEP SEPARATE"
                results.append({
                    "node_type": node_type,
                    "group_number": idx,
                    "decision": decision,
                    "input_nodes": nodes,
                    "ids": ids,
                    "mapping": mapping
                })

        merged_groups_by_type[node_type] = merged_groups
    # Save detailed results
    with open("llm_dedup_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    # Save merged_groups_by_type.json for downstream processing
    with open("merged_groups_by_type.json", "w", encoding="utf-8") as f:
        json.dump(merged_groups_by_type, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
