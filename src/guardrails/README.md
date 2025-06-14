# Guardrail Details in the System

## 1. PromptInjectionGuardrail
**Purpose:**
- Detects and prevents prompt injection attacks in input and output using both regex patterns and NLP techniques (spaCy).

**Mechanism:**
- Input is checked in 3 layers:
  1. **Regex Pattern:** Detects high-risk phrases such as "ignore previous instructions", "act as", "jailbreak", etc.
  2. **NLP-based Keyword & Intent:** Uses spaCy to analyze word lemmas for trigger words (e.g., ignore, jailbreak, sudo, etc.) and detects sentence structures with verb + sensitive object (e.g., "reveal password").
  3. **Heuristic:** Checks the ratio of special characters and input length.

**Result:**
- If the input is deemed risky for prompt injection, it returns (False, reason) and **does not modify/redact the text**.
- If the input is safe, it returns (True, None).

**Why there is no redacted_input:**
- Prompt injection detection blocks risky input immediately rather than attempting to sanitize it, because redacting may not fully eliminate the threat (e.g., sentence structure or intent).
- Therefore, the original input is sent to the error_node with the reason, and no redacted_input is provided.

**Output checking:**
- Uses the same patterns as input. If detected, it attempts to sanitize (e.g., replaces forbidden phrases with [FILTERED]).

---

## 2. SensitiveInfoGuardrail
**Purpose:**
- Detects and redacts sensitive information (e.g., credit card numbers, passwords, phone numbers, emails, national IDs, etc.) in input and output.

**Mechanism:**
- Layer 1: Regex patterns for each sensitive data type (credit card, ssn, phone, email, api key, etc.)
- Layer 2: Checks for keywords commonly associated with sensitive data (e.g., password: xxxxx)
- Layer 3: Uses spaCy to detect entities (PERSON, ORG, GPE, MONEY, etc.) and analyzes the surrounding context to assess risk
- Layer 4: Checks dependency patterns such as "my password is ..."

**Result:**
- If sensitive information is found, returns redacted_input/redacted_output where sensitive data is replaced with [REDACTED] and provides findings.
- If no sensitive information is found, returns the original text.

---

## 3. GuardrailManager
- Serves as the orchestrator for both types of guardrails above.
- `validate_input` checks prompt injection first (blocks immediately if detected), then sensitive info (redacts if necessary).
- `process_output` sanitizes output using both guardrails.

---

### Summary: 
- Prompt injection guardrail does not provide redacted_input because sanitizing the text cannot guarantee safety; risky input must be blocked immediately. Sensitive info guardrail can redact because the data patterns are clear and redaction does not affect the main logic of the text.