from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, root_validator

class LLMResponse(BaseModel):
    action: str
    best_name: Optional[str] = None
    aliases: Optional[List[str]] = None
    merged_fields: Optional[Dict[str, Any]] = None
    justification: Optional[str] = None

    @staticmethod
    def clean_merged_fields(mf: dict) -> dict:
        # For description and significance, prefer the string value if both string and list exist
        for field in ["description", "significance"]:
            if field in mf:
                val = mf[field]
                # If both a string and a list exist (from LLM JSON quirks), keep only the string
                if isinstance(val, list):
                    # Remove if there is also a string version elsewhere (shouldn't happen after json.loads, but just in case)
                    # Optionally join all strings in the list, or just use the first
                    mf[field] = " ".join([str(x) for x in val if isinstance(x, str)])
        # Remove duplicate keys (shouldn't be possible in a dict, but if LLM returns as list of tuples, handle here)
        return mf

    @root_validator(pre=True)
    def ensure_synthesized_fields_are_strings(cls, values):
        mf = values.get('merged_fields', {})
        if isinstance(mf, dict):
            values['merged_fields'] = cls.clean_merged_fields(mf)
        return values
