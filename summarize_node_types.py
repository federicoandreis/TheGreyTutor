import os
from neo4j import GraphDatabase
from tabulate import tabulate

# Load Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Node types to summarize
TARGET_LABELS = [
    "Artifact",
    "Character",
    "Community",
    "Event",
    "Location",
    "Organization",
]

from collections import Counter, defaultdict

def get_node_and_duplicate_counts(uri, user, password, labels):
    from collections import defaultdict
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(uri, auth=(user, password))
    session = driver.session()
    summary = []
    node_counts = {}
    nodes_by_type = {}
    for label in labels:
        nodes = []
        result = session.run(f"MATCH (n:`{label}`) RETURN elementId(n) as id, n as props")
        for record in result:
            node = dict(record["props"])
            node["id"] = record["id"]
            nodes.append(node)
        nodes_by_type[label] = nodes
        node_counts[label] = len(nodes)
    duplicate_nodes_by_type = {label: [] for label in labels}
    all_duplicate_node_ids = set()
    for label in labels:
        summary_row = [label, node_counts[label], 0, 0]
        name_to_nodes = defaultdict(list)
        alias_to_nodes = defaultdict(list)
        for node in nodes_by_type[label]:
            node_id = node["id"]
            name = node.get("name", "")
            # Handle name being a list or a string
            if isinstance(name, list):
                name = " ".join([n for n in name if isinstance(n, str) and n.strip()])
            if isinstance(name, str) and name.strip():
                name_to_nodes[name.strip().lower()].append((node_id, node))
            for alias in node.get("aliases", []) or []:
                # Handle alias being a list or a string
                if isinstance(alias, list):
                    alias = " ".join([a for a in alias if isinstance(a, str) and a.strip()])
                if isinstance(alias, str) and alias.strip():
                    alias_to_nodes[alias.strip().lower()].append((node_id, node))
        # Initial groups by name and alias
        raw_groups = []
        for group in name_to_nodes.values():
            if len(group) > 1:
                raw_groups.append(set(node_id for node_id, _ in group))
                summary_row[2] += 1
                all_duplicate_node_ids.update([node_id for node_id, _ in group])
        for group in alias_to_nodes.values():
            if len(group) > 1:
                raw_groups.append(set(node_id for node_id, _ in group))
                summary_row[3] += 1
                all_duplicate_node_ids.update([node_id for node_id, _ in group])
        # Merge groups that share node IDs (transitive closure)
        def merge_groups(groups):
            merged = []
            while groups:
                first, *rest = groups
                first = set(first)
                changed = True
                while changed:
                    changed = False
                    rest2 = []
                    for g in rest:
                        if first & g:
                            first |= g
                            changed = True
                        else:
                            rest2.append(g)
                    rest = rest2
                merged.append(first)
                groups = rest
            return merged
        merged_groups = merge_groups(raw_groups)
        # Build final duplicate groups for LLM
        node_lookup = {node["id"]: node for node in nodes_by_type[label]}
        duplicate_groups = []
        for group in merged_groups:
            group_nodes = [node_lookup[nid] for nid in group if nid in node_lookup]
            # Use the first node's name/alias for display
            display_val = group_nodes[0].get("name") or (group_nodes[0].get("aliases") or [''])[0]
            duplicate_groups.append({
                "duplicate_type": "transitive_duplicate",
                "value": display_val,
                "nodes": group_nodes
            })
        duplicate_nodes_by_type[label] = duplicate_groups
        summary.append(summary_row)
    driver.close()
    return summary, duplicate_nodes_by_type, all_duplicate_node_ids

import json
import os
from llm_response_model import LLMResponse
from pydantic import ValidationError

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] python-dotenv not installed. .env file will not be loaded.")

# Optional: LLM integration
import requests

def call_llm_judge_duplicates(duplicate_group, node_type, openai_api_key=None):
    """
    Calls the LLM to judge whether to merge or keep duplicates separate.
    """
    prompt = f"""
You are a Tolkien lore expert and a knowledge graph curation specialist. Your task is to judge whether the following suspected duplicate {node_type} nodes represent the SAME canonical entity in Tolkien's legendarium.

**STRICT GUIDELINES:**
- Only merge nodes if they refer to the exact same unique entity (character, artifact, event, etc.) as recognized in Tolkien's works.
- Do NOT merge nodes just because they share similar properties (such as race, home, last name, or even both being ring-bearers).
- For example, do NOT merge 'Frodo Baggins' and 'Bilbo Baggins'—they are different characters despite both being hobbits from Hobbiton and both being ring-bearers.
- If you recommend merging, provide a strong justification referencing canonical sources or lore. If not, explain why they should remain separate.
- If you are unsure, err on the side of keeping nodes separate.

**Task:**
1. Decide if these nodes should be coalesced into a single entry or kept as separate entries. Consider spelling, capitalization, context, and all available properties.
2. If merging, pick the best name (prefer full, canonical, capitalized names; avoid abbreviations unless canonical). All other names should be added to the aliases list, deduplicated in a case-insensitive way (treat "Gold" and "gold" as the same), but preserve the original casing of the first occurrence.
3. For fields like 'current_status' or others that may have conflicting or temporal values, coalesce all unique values into a list, deduplicated in a case-insensitive way and preserving order if possible.
4. For all other fields, merge sensibly, preferring the most complete or canonical value, and include all unique values in lists where appropriate, deduplicated in a case-insensitive way.
5. **If merging, synthesize a new 'description' and 'significance' field for the merged node, using all available information from the group. Write these as natural-language sentences that combine the facts from the original nodes. For example, if merging nodes with descriptions 'Elven refuge' and 'Hidden valley', the merged description could be 'Rivendell is one of the great Elven refuges, located in a hidden valley.'**
6. Justify your decision, referencing specific properties, context, or canonical sources as needed.

Suspected duplicates:
{json.dumps(duplicate_group, indent=2, ensure_ascii=False)}

Respond ONLY with a JSON object with the following keys:
- action: 'merge' or 'separate'
- best_name: (if merging) the chosen name
- aliases: (if merging) list of aliases
- merged_fields: (if merging) dictionary of merged fields (all merged properties, including synthesized 'description' and 'significance')
- justification: your reasoning
"""
    if not openai_api_key:
        print("[LLM MOCK] No OpenAI API key provided. Skipping real LLM call.")
        print(f"Prompt would be:\n{prompt}\n")
        return {"action": "mock", "justification": "No API key, so this is a mock response."}
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for knowledge graph curation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    import re
    try:
        response_json = response.json()
        if "choices" not in response_json:
            print("[DEBUG] LLM API full response:", response_json)
            return {"error": "LLM API error: missing 'choices' in response", "raw": response_json}
        llm_content = response_json["choices"][0]["message"]["content"]
        # Try to parse JSON, stripping code block markers if needed
        def try_parse_json(text):
            # Remove all code block markers and extra whitespace
            import re
            # Remove any ```json or ``` at the start/end (with or without whitespace)
            codeblock_regex = r"^```(?:json)?[ \t]*\n?|```[ \t]*$"
            stripped = re.sub(codeblock_regex, "", text.strip(), flags=re.IGNORECASE|re.MULTILINE).strip()
            try:
                return json.loads(stripped)
            except Exception as e:
                print("[DEBUG] Failed to parse LLM JSON. Attempted string:")
                print(stripped)
                raise
        try:
            llm_data = try_parse_json(llm_content)
        except Exception:
            return {"error": "Could not parse LLM response as JSON", "raw": llm_content}
        # Post-process merged_fields to remove duplicate description/significance
        if isinstance(llm_data, dict) and 'merged_fields' in llm_data:
            llm_data['merged_fields'] = LLMResponse.clean_merged_fields(llm_data['merged_fields'])
        # Validate and safetype using Pydantic (v2+)
        try:
            validated = LLMResponse.model_validate(llm_data)
            return validated.model_dump()
        except ValidationError as ve:
            return {"error": f"LLM response failed validation: {ve}", "raw": llm_data}
    except Exception as e:
        print("[DEBUG] LLM API exception:", e)
        return {"error": f"LLM API error: {e}", "raw": str(e)}

def fetch_node_properties(uri, user, password, node_ids_by_type):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    node_props_by_type = {label: {} for label in node_ids_by_type}
    with driver.session() as session:
        for label, element_ids in node_ids_by_type.items():
            if not element_ids:
                continue
            # Use UNWIND for efficient property extraction
            query = f"""
                UNWIND $ids AS element_id
                MATCH (n:`{label}`)
                WHERE elementId(n) = element_id
                RETURN elementId(n) AS element_id, properties(n) AS props
            """
            result = session.run(query, ids=list(element_ids))
            for record in result:
                node_props_by_type[label][record["element_id"]] = record["props"]
    driver.close()
    return node_props_by_type

def main():
    summary, duplicate_nodes_by_type, all_duplicate_node_ids = get_node_and_duplicate_counts(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, TARGET_LABELS)
    print("\nNode counts and duplicates by type:\n")
    print(tabulate(summary, headers=["Node Type", "Total", "Duplicate Names", "Duplicate Aliases"], tablefmt="github"))
    print()

    # Build a mapping: label -> set(node_ids) for duplicates
    node_ids_by_type = {label: set() for label in TARGET_LABELS}
    for label in TARGET_LABELS:
        dups = duplicate_nodes_by_type[label]
        for group in dups:
            node_ids_by_type[label].update([node_id for node_id, _ in [(n['id'], n) for n in group['nodes']]])

    # Fetch all properties for duplicate nodes
    node_props_by_type = fetch_node_properties(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, node_ids_by_type)

    # Build the {duplicates} structure
    duplicates = {label: [] for label in TARGET_LABELS}
    for label in TARGET_LABELS:
        dups = duplicate_nodes_by_type[label]
        for group in dups:
            group_entry = {
                "duplicate_type": group["duplicate_type"],
                "value": group["value"],
                "nodes": [
                    {"id": n["id"], **node_props_by_type[label].get(n["id"], {})}
                    for n in group["nodes"]
                ]
            }
            duplicates[label].append(group_entry)
    # print("\n{duplicates} (for LLM input):\n")
    # print(json.dumps(duplicates, indent=2, ensure_ascii=False))
    # print("")

    # --- LLM Judgement Call ---
    openai_api_key = os.getenv("OPENAI_API_KEY")
    any_duplicates = any(len(groups) > 0 for groups in duplicates.values())
    if not any_duplicates:
        print("No suspected duplicates. Skipping LLM call.")
        return
    print("\nCalling LLM to judge each group of suspected duplicates...\n")
    # --- Case-insensitive deduplication utility ---
    def deduplicate_case_insensitive(seq):
        seen = set()
        result = []
        for item in seq:
            key = item.lower() if isinstance(item, str) else item
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def deduplicate_merged_fields(llm_result):
        # Deduplicate aliases
        if "aliases" in llm_result and isinstance(llm_result["aliases"], list):
            llm_result["aliases"] = deduplicate_case_insensitive(llm_result["aliases"])
        # Deduplicate all lists in merged_fields
        if "merged_fields" in llm_result and isinstance(llm_result["merged_fields"], dict):
            for k, v in llm_result["merged_fields"].items():
                if isinstance(v, list):
                    llm_result["merged_fields"][k] = deduplicate_case_insensitive(v)
        return llm_result

    # --- Review/Approval Workflow (Mock for now) ---
    def review_and_approve_llm_result(llm_result, group, label):
        """
        Mock approval workflow. Always approves for now.
        TODO: Implement real review/approval workflow with user input or external system.
        """
        print("[REVIEW MOCK] Automatically approving LLM decision for group.")
        return True

    for node_type in TARGET_LABELS:
        groups = duplicates.get(node_type, [])
        if not groups:
            continue
        print(f"\n--- Processing node type: {node_type} ---")
        for group in groups:
            node_names = [n.get('name', '') for n in group.get('nodes', [])]
            print(f"[SUMMARY] {node_type}: Comparing suspected duplicates: {', '.join(repr(n) for n in node_names)} (by {group['duplicate_type']}='{group['value']}')")
            llm_result = call_llm_judge_duplicates(group, node_type, openai_api_key=openai_api_key)
            llm_result = deduplicate_merged_fields(llm_result)
            # Only summarize the final resolution
            if llm_result.get('action') in ('merge', 'separate'):
                print(f"[RESOLUTION] {node_type}: {llm_result['action'].upper()}\n  Best Name: {llm_result.get('best_name', '-')}")
                justification = llm_result.get("justification")
                if not justification:
                    justification = "No justification provided."
                print(f"  Justification: {justification}")
            else:
                print(f"[LLM ERROR] {node_type}: {llm_result.get('error', 'Unknown error')}")
                if 'raw' in llm_result:
                    print(f"  Raw LLM output: {llm_result['raw']}")
            approved = review_and_approve_llm_result(llm_result, group, node_type)
            if approved:
                print(f"[APPROVED] {node_type}: This LLM judgment is approved for further action.\n")
            else:
                print(f"[NOT APPROVED] {node_type}: This LLM judgment was not approved.\n")
            print()

if __name__ == "__main__":
    main()
