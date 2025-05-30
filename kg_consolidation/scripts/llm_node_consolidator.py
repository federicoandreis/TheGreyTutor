"""
Agent: LLM Node Consolidator

Reads merged_groups_by_type.json and, for each group of nodes to be merged, orchestrates:
- Extraction of all node properties and relationships from Neo4j
- Selection of the best reference node
- LLM-driven merging of properties and relationships (prompt inspired by summarize_node_types.py)
- Application of the merge: update reference node, reattach relationships, delete merged nodes

If all merge indices are unique for a group, skips that group.

This agent is designed to be orchestrated with smolagents, and to operate in a pipeline after llm_group_dedup_decision.py.
"""
import json
from typing import List, Dict, Any
from neo4j import GraphDatabase
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional, but recommended for .env support
# from openai import OpenAI # Uncomment and configure as needed
# from smolagents import Agent, Task # Uncomment if using smolagents

MERGED_GROUPS_FILE = "merged_groups_by_type.json"

class LLMNodeConsolidator:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # self.llm_client = OpenAI(api_key=...) # Configure as needed

    def process(self):
        import datetime
        log_file = 'merge_log.txt'
        processed, merged, skipped, removed = 0, 0, 0, 0
        log_lines = []
        import time
        start_time = time.time()
        with open(MERGED_GROUPS_FILE, "r", encoding="utf-8") as f:
            merged_groups_by_type = json.load(f)
        any_groups = any(merged_groups_by_type.get(k) for k in merged_groups_by_type)
        if not any_groups:
            print('[INFO] No groups left to process.')
            return
        total_types = len(merged_groups_by_type)
        print(f"[START] Node consolidation for {total_types} node types.")
        for node_type, groups in merged_groups_by_type.items():
            num_groups = len(groups)
            print(f"[TYPE] Processing '{node_type}' ({num_groups} groups to check)")
            for idx, group in enumerate(groups):
                ids = group["nodes"]
                mapping = group["merge"]
                if len(set(mapping)) == len(mapping):
                    # Only print if a group is skipped
                    print(f"[SKIP] '{node_type}' group {idx+1}/{num_groups}: no duplicates.")
                    skipped += 1
                    continue
                try:
                    node_infos = self._extract_node_info(ids)
                    if not node_infos:
                        print(f"[WARN] '{node_type}' group {idx+1}/{num_groups}: no nodes found in Neo4j.")
                        skipped += 1
                        continue
                    ref_idx = self._choose_reference_node(node_infos)
                    merged_info = self._llm_merge_nodes(node_type, node_infos, ref_idx)
                    ref_id = node_infos[ref_idx]['id']
                    to_merge_ids = [n['id'] for i, n in enumerate(node_infos) if i != ref_idx]
                    self._apply_merge_to_neo4j(ref_id, to_merge_ids, merged_info)
                    merged += 1
                    removed += 1
                except Exception as e:
                    print(f"[ERROR] '{node_type}' group {idx+1}/{num_groups}: {e}")
                    skipped += 1
                processed += 1
                # Progress log every 10 groups or at end
                if (idx + 1) % 10 == 0 or (idx + 1) == num_groups:
                    elapsed = time.time() - start_time
                    eta = (elapsed / (idx + 1)) * (num_groups - (idx + 1)) if idx + 1 > 0 else 0
                    print(f"[PROGRESS] '{node_type}' {idx+1}/{num_groups} groups processed. Elapsed: {elapsed:.1f}s, ETA: {eta:.1f}s")
        print(f"\n[SUMMARY] Processed: {processed}, Merged: {merged}, Skipped: {skipped}, Removed: {removed}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[SUMMARY] {datetime.datetime.now().isoformat()}\tProcessed: {processed}, Merged: {merged}, Skipped: {skipped}, Removed: {removed}\n")

    def _process_group(self, node_type: str, ids: List[str], mapping: List[int]):
        """For each subgroup with the same merge index, perform extraction and merge."""

    def _extract_node_info(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch all properties and relationships for each node from Neo4j.
        Returns a list of dicts with node properties and relationships.
        """
        results = []
        with self.driver.session() as session:
            for nid in node_ids:
                # Fetch node properties
                node_query = """
                MATCH (n) WHERE elementId(n) = $nid
                RETURN elementId(n) as id, labels(n) as labels, n as props
                """
                node_result = session.run(node_query, nid=nid).single()
                if not node_result:
                    continue
                node_props = dict(node_result["props"])
                node_info = {
                    'id': node_result["id"],
                    'labels': node_result["labels"],
                }
                node_info.update(node_props)
                # Fetch outgoing relationships
                out_query = """
                MATCH (n)-[r]->(m) WHERE elementId(n) = $nid
                RETURN type(r) as type, elementId(m) as target_id, properties(r) as properties
                """
                outgoing = [dict(r) for r in session.run(out_query, nid=nid)]
                # Fetch incoming relationships
                in_query = """
                MATCH (n)<-[r]-(m) WHERE elementId(n) = $nid
                RETURN type(r) as type, elementId(m) as source_id, properties(r) as properties
                """
                incoming = [dict(r) for r in session.run(in_query, nid=nid)]
                node_info['outgoing_relationships'] = outgoing
                node_info['incoming_relationships'] = incoming
                results.append(node_info)
        return results

    def _choose_reference_node(self, node_infos: List[Dict[str, Any]]) -> int:
        """
        Pick the node with the longest description as the reference. If 'description' is missing, treat as empty string.
        """
        return max(range(len(node_infos)), key=lambda i: len(node_infos[i].get('description', '')))

    def _llm_merge_nodes(self, node_type: str, node_infos: List[Dict[str, Any]], ref_idx: int) -> Dict[str, Any]:
        """
        Use LLM to merge properties and relationships.
        Prompt is inspired by summarize_node_types.py and tailored for canonical entity consolidation.
        - Provide all properties and relationships for all nodes.
        - Ask for the best name (unique), amalgamate other fields (aliases, descriptions, significance, etc.).
        - Relationships should be deduplicated and preserved.
        - Output format: JSON with all merged properties and relationships, plus a justification.
        """
        import json as _json
        prompt = f"""
You are a Tolkien lore expert and a knowledge graph curation specialist. Your task is to merge the following suspected duplicate {node_type} nodes into a single canonical entity in Tolkien's legendarium.

**STRICT GUIDELINES:**
- Only merge nodes if they refer to the exact same unique entity (character, artifact, event, etc.) as recognized in Tolkien's works.
- For each property (name, aliases, description, significance, etc.), keep the best or most canonical value as the main value, and amalgamate all others as aliases or appended info.
- The resulting node must have a single unique name, but can have multiple aliases, descriptions, etc.
- Deduplicate and preserve all relationships (edges) to other nodes.
- Output a single JSON object with all merged properties and relationships, and a short justification for your merge decisions.

**Task:**
1. Review all properties and relationships for the following nodes:
"""
        all_names = set()
        for i, node in enumerate(node_infos):
            prompt += f"\nNode {i+1}: {_json.dumps(node, ensure_ascii=False)}"
            if 'name' in node and node['name']:
                name_field = node['name']
                if isinstance(name_field, list):
                    for n in name_field:
                        if isinstance(n, str):
                            all_names.add(n.strip().lower())
                elif isinstance(name_field, str):
                    all_names.add(name_field.strip().lower())
            for alias in node.get('aliases', []):
                if isinstance(alias, str):
                    all_names.add(alias.strip().lower())

        prompt += (
            "\n\nRespond ONLY with a single valid JSON object in the format below, and NOTHING else. "
            "Do NOT include any commentary, markdown, explanation, or triple backticks. "
            "Do NOT wrap your response in any code block. "
            "If you cannot merge, reply with an empty JSON object {}. "
            "\nFORMAT REQUIREMENTS (CRITICAL):\n"
            "- The merged node's 'aliases' field MUST include every unique name and alias from all input nodes, including 'The One Ring' and all its variants, even if they are similar or redundant.\n"
            "- Never lose or drop any variant of the name 'The One Ring' or its known aliases.\n"
            "- If any node has 'one ring' (case-insensitive) in its name or aliases, it MUST appear in either the merged node's name or aliases.\n"
            "- Output a single JSON object with all merged properties and relationships, and a short justification.\n"
            "\nFormat:\n{\n  \"name\": <best_name>,\n  \"aliases\": [...],\n  \"description\": <merged_description>,\n  \"significance\": <merged_significance>,\n  \"outgoing_relationships\": [...],\n  \"incoming_relationships\": [...],\n  \"justification\": <short explanation>\n}\n"
        )
        try:
            from openai import OpenAI
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ImportError("OPENAI_API_KEY environment variable not set.")
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a Tolkien knowledge graph curation expert."}, {"role": "user", "content": prompt}],
                max_tokens=2048, temperature=0
            )
            answer = response.choices[0].message.content.strip()
            import re
            cleaned = answer.strip()
            cleaned = re.sub(r'^```[a-zA-Z]*', '', cleaned)
            cleaned = re.sub(r'```$', '', cleaned)
            cleaned = cleaned.strip()
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = cleaned
            # Detect truncation: unmatched braces or ends mid-list/object
            def is_truncated(s):
                open_braces = s.count('{')
                close_braces = s.count('}')
                return close_braces < open_braces or s.rstrip()[-1] not in ['}', ']']
            if is_truncated(json_str):
                # Retry with a continuation prompt
                print("[LLM] Output appears truncated. Requesting continuation from LLM...")
                continuation_prompt = "Your previous response was cut off. Please continue and respond ONLY with the remainder of the JSON object, starting exactly where you left off. Do not repeat any content, and do not include any commentary or markdown."
                continuation_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are a Tolkien knowledge graph curation expert."},
                              {"role": "user", "content": prompt},
                              {"role": "assistant", "content": answer},
                              {"role": "user", "content": continuation_prompt}],
                    max_tokens=1024, temperature=0
                )
                continuation = continuation_response.choices[0].message.content.strip()
                # Clean and concatenate
                continuation_cleaned = continuation.strip()
                continuation_cleaned = re.sub(r'^```[a-zA-Z]*', '', continuation_cleaned)
                continuation_cleaned = re.sub(r'```$', '', continuation_cleaned)
                continuation_cleaned = continuation_cleaned.strip()
                combined = json_str + continuation_cleaned
                # Try to extract the full JSON again
                json_match2 = re.search(r'\{[\s\S]*\}', combined)
                if json_match2:
                    combined_json_str = json_match2.group(0)
                else:
                    combined_json_str = combined
                try:
                    merged = _json.loads(combined_json_str)
                except Exception:
                    print("[LLM] Could not parse response even after continuation. Partial output was:")
                    print(combined)
                    merged = {"llm_output": combined}
                return merged
            else:
                merged = _json.loads(json_str)
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return {}
        # ENFORCE: All original names/aliases must be present in merged['aliases'] or merged['name']
        merged_aliases = set(a.strip().lower() for a in merged.get('aliases', []))
        missing = [n for n in all_names if n not in merged_aliases and n != merged.get('name', '').strip().lower()]
        if missing:
            import warnings
            warnings.warn(f"Merged node missing original names/aliases: {missing}. Adding them to aliases.")
            merged['aliases'] = list(merged.get('aliases', [])) + missing
        # Always ensure 'one ring' is present in name or aliases if it was present in any input
        if any('one ring' in n for n in all_names):
            if 'one ring' not in merged.get('name', '').lower() and not any('one ring' in a for a in merged.get('aliases', [])):
                merged['aliases'] = list(merged.get('aliases', [])) + ['The One Ring']
        return merged

    def _apply_merge_to_neo4j(self, ref_id: str, to_merge_ids: List[str], merged_info: Dict[str, Any]):
        """
        Apply the merged properties and relationships to the reference node in Neo4j, and delete merged nodes.
        This method performs REAL writes to the Neo4j database.
        Only adds new relationships not already present; does not delete any relationships from the reference node.
        """
        with self.driver.session() as session:
            # Update properties
            set_props = {k: v for k, v in merged_info.items() if k not in ('outgoing_relationships', 'incoming_relationships', 'justification')}
            set_clause = ', '.join([f"n.{k} = ${k}" for k in set_props.keys()])
            session.run(f"MATCH (n) WHERE elementId(n) = $ref_id SET {set_clause}", ref_id=ref_id, **set_props)

            # Fetch existing outgoing relationships
            existing_outgoing = set()
            for record in session.run("MATCH (n)-[r]->(m) WHERE elementId(n) = $ref_id RETURN type(r) as type, elementId(m) as target_id, properties(r) as properties", ref_id=ref_id):
                key = (record['type'], record['target_id'], frozenset(record['properties'].items()))
                existing_outgoing.add(key)

            # Add only missing outgoing relationships
            for rel in merged_info.get('outgoing_relationships', []):
                key = (rel['type'], rel['target_id'], frozenset(rel.get('properties', {}).items()))
                if key not in existing_outgoing:
                    session.run(
                        "MATCH (n), (m) WHERE elementId(n) = $ref_id AND elementId(m) = $target_id "
                        "CREATE (n)-[r:%s]->(m) SET r = $properties" % rel['type'],
                        ref_id=ref_id, target_id=rel['target_id'], properties=rel.get('properties', {})
                    )

            # Fetch existing incoming relationships
            existing_incoming = set()
            for record in session.run("MATCH (m)-[r]->(n) WHERE elementId(n) = $ref_id RETURN type(r) as type, elementId(m) as source_id, properties(r) as properties", ref_id=ref_id):
                key = (record['type'], record['source_id'], frozenset(record['properties'].items()))
                existing_incoming.add(key)

            # Add only missing incoming relationships
            for rel in merged_info.get('incoming_relationships', []):
                key = (rel['type'], rel['source_id'], frozenset(rel.get('properties', {}).items()))
                if key not in existing_incoming:
                    session.run(
                        "MATCH (m), (n) WHERE elementId(m) = $source_id AND elementId(n) = $ref_id "
                        "CREATE (m)-[r:%s]->(n) SET r = $properties" % rel['type'],
                        source_id=rel['source_id'], ref_id=ref_id, properties=rel.get('properties', {})
                    )

            # Delete merged duplicate nodes
            for node_id in to_merge_ids:
                session.run("MATCH (n) WHERE elementId(n) = $node_id DETACH DELETE n", node_id=node_id)

            # Log DB write
            print(f"[DB WRITE] Updated node {ref_id}, deleted nodes {to_merge_ids}")

if __name__ == "__main__":
    # Example usage (fill in Neo4j credentials)
    consolidator = LLMNodeConsolidator(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    consolidator.process()
