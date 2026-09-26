# Structured outputs

Roles that feed later phases return a JSON block, fenced as `json`, after their markdown write-up. The orchestrator extracts it, validates it against these schemas, and asks the role to fix the block if it is invalid. Hosts that support structured output may pass the schemas directly.

## Contents

1. Hypothesis ledger row
2. Generator output
3. Red-team output
4. Verifier output

## 1. Hypothesis ledger row

The investigators return an array of these, one per hypothesis in their family. The ledger in `work/ledger.json` is the merged array.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["hypothesis", "family", "status", "confidence_in_status", "probability_band", "stakes",
               "one_line", "strongest_for", "strongest_against", "next_tests"],
  "properties": {
    "hypothesis": {"type": "string"},
    "family": {"type": "string"},
    "status": {"enum": ["excluded", "unlikely", "open", "supported", "untested"]},
    "confidence_in_status": {"enum": ["low", "moderate", "high"]},
    "probability_band": {"enum": ["very low", "low", "moderate", "high"]},
    "stakes": {"enum": ["low", "moderate", "high"]},
    "one_line": {"type": "string"},
    "strongest_for": {"type": "string", "description": "with [n] citations"},
    "strongest_against": {"type": "string", "description": "with [n] citations"},
    "test_adequacy_issues": {"type": "string"},
    "shares_failure_mode_with": {"type": "array", "items": {"type": "string"}},
    "next_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["test", "burden", "discriminates"],
        "properties": {
          "test": {"type": "string"},
          "specimen_or_procedure": {"type": "string"},
          "burden": {"enum": ["held-specimen", "blood", "urine", "imaging", "bedside", "new-procedure", "tissue", "other"]},
          "discriminates": {"type": "string", "description": "what a positive and a negative would mean"}
        }
      }
    },
    "sources": {"type": "array", "items": {"type": "string"}}
  }
}
```

## 2. Generator output

```json
{
  "type": "object",
  "required": ["entry_point", "hypotheses"],
  "properties": {
    "entry_point": {"type": "string"},
    "hypotheses": {
      "type": "array", "minItems": 20,
      "items": {
        "type": "object",
        "required": ["hypothesis", "fit", "conflict", "tests_already_bearing"],
        "properties": {
          "hypothesis": {"type": "string"},
          "is_mechanism": {"type": "boolean", "description": "true if it explains the main symptom's mechanism rather than the cause"},
          "fit": {"type": "string"},
          "conflict": {"type": "string"},
          "tests_already_bearing": {"type": "string"}
        }
      }
    },
    "unexplained_findings": {"type": "array", "items": {"type": "string"}}
  }
}
```

## 3. Red-team output

```json
{
  "type": "object",
  "required": ["role", "challenges", "new_hypotheses"],
  "properties": {
    "role": {"enum": ["attack-leader", "attack-exclusions", "attack-framing", "completeness"]},
    "challenges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["target", "claim", "severity", "proposed_change"],
        "properties": {
          "target": {"type": "string", "description": "hypothesis or ledger field challenged"},
          "claim": {"type": "string"},
          "severity": {"enum": ["low", "moderate", "high"]},
          "proposed_change": {"type": "string"}
        }
      }
    },
    "new_hypotheses": {"type": "array", "items": {"type": "string"}}
  }
}
```

## 4. Verifier output

```json
{
  "type": "object",
  "required": ["assertions_checked", "issues"],
  "properties": {
    "assertions_checked": {"type": "integer"},
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["location", "exact_text", "problem", "severity", "correction"],
        "properties": {
          "location": {"type": "string"},
          "exact_text": {"type": "string"},
          "problem": {"enum": ["wrong-number", "wrong-unit", "wrong-date", "wrong-attribution", "unsupported",
                                "absence-claim-false", "citation", "literature", "style", "directive", "other"]},
          "severity": {"enum": ["low", "medium", "high"]},
          "correction": {"type": "string"},
          "evidence": {"type": "string", "description": "file and line that settles it"}
        }
      }
    }
  }
}
```
