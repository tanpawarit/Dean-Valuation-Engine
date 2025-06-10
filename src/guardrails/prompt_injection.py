"""
Prompt Injection Guardrail

This module provides protection against prompt injection attacks by detecting and
filtering potentially malicious input patterns using both regex pattern matching
and NLP-based techniques with spaCy.
"""

import re
import spacy
from typing import List, Optional, Pattern, Set, Tuple 
from functools import lru_cache


@lru_cache(maxsize=1)
def load_nlp_model() -> spacy.language.Language:
    """
    Load the spaCy model with caching to avoid repeated loading.
    
    Returns:
        A loaded spaCy language model
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # If model isn't installed, download it
        import subprocess
        import sys
        
        print("Downloading spaCy model (this may take a moment)...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        return spacy.load("en_core_web_sm")


class PromptInjectionGuardrail:
    """
    A guardrail to detect and prevent prompt injection attacks.
    
    This class implements advanced pattern matching and NLP-based detection to identify
    common prompt injection techniques using both regex patterns and semantic analysis.
    """
    
    def __init__(self) -> None:
        """Initialize the prompt injection guardrail with detection patterns."""
        # 1. Regex patterns for obvious, high-risk attacks
        self.injection_patterns: List[Pattern[str]] = [
            # System prompt leakage attempts
            re.compile(r"ignore previous instructions", re.IGNORECASE),
            re.compile(r"disregard (all|previous|your) instructions", re.IGNORECASE),
            re.compile(r"forget (all|previous|your) instructions", re.IGNORECASE),
            re.compile(r"ignore (all|previous|your) constraints", re.IGNORECASE),
            re.compile(r"system prompt", re.IGNORECASE),
            re.compile(r"you are now", re.IGNORECASE),
            re.compile(r"your new role is", re.IGNORECASE),
            re.compile(r"act as", re.IGNORECASE),
            re.compile(r"pretend to be", re.IGNORECASE),
            re.compile(r"you're no longer", re.IGNORECASE),
            
            # Delimiter attacks
            re.compile(r"<\s*/?(system|user|assistant)\s*>", re.IGNORECASE),
            re.compile(r"\[\s*/?(system|user|assistant)\s*\]", re.IGNORECASE),
            
            # Code execution attempts
            re.compile(r"os\.(system|popen|exec)", re.IGNORECASE),
            re.compile(r"subprocess\.(call|run|Popen)", re.IGNORECASE),
            
            # Jailbreak attempts
            re.compile(r"DAN", re.IGNORECASE),  # Do Anything Now
            re.compile(r"STAN", re.IGNORECASE),  # Strive To Avoid Norms
            re.compile(r"jailbreak", re.IGNORECASE),
            re.compile(r"dev mode", re.IGNORECASE),
            re.compile(r"developer mode", re.IGNORECASE),
            re.compile(r"sudo mode", re.IGNORECASE),
        ]
        
        # 2. NLP-based keyword detection
        self.keyword_triggers: Set[str] = {
            "ignore", "disregard", "forget", "pretend", "act",
            "jailbreak", "dan", "stan", "sudo", "developer", "admin"
        }
        
        # Action verbs that might indicate malicious intent
        self.action_verbs: Set[str] = {
            "print", "reveal", "tell", "show", "give", "display", "expose", 
            "share", "leak", "bypass", "override", "hack"
        }
        
        # Sensitive targets that shouldn't be accessed
        self.sensitive_objects: Set[str] = {
            "instruction", "prompt", "rule", "guideline", "constraint", 
            "password", "secret", "system", "code", "internal", "config"
        }
        
        # Heuristic thresholds
        self.max_special_char_ratio: float = 0.3  # Maximum ratio of special characters
        self.max_input_length: int = 4096  # Maximum input length
        
    def process_input(self, input_text: str) -> Tuple[bool, Optional[str]]:
        """
        Process input text to detect potential prompt injection attacks using
        multi-layered detection with both regex and NLP techniques.
        
        Args:
            input_text: The text to check for prompt injection patterns
            
        Returns:
            Tuple of (is_safe, reason) where:
                - is_safe: Boolean indicating if the input is safe
                - reason: If not safe, the reason for rejection, otherwise None
        """
        if not input_text or not isinstance(input_text, str):
            return False, "Input must be a non-empty string"
            
        # --- Layer 1: Fast Regex Check ---
        for pattern in self.injection_patterns:
            if pattern.search(input_text):
                return False, f"Potential prompt injection detected: {pattern.pattern}"
        
        # --- Layer 2: NLP-based Keyword and Intent Check ---
        try:
            # Load the NLP model
            nlp = load_nlp_model()
            
            # Process the text with spaCy
            doc = nlp(input_text.lower())
            
            # Extract lemmas (base forms of words)
            lemmas = {token.lemma_ for token in doc}
            
            # Check for trigger keywords
            matched_keywords = self.keyword_triggers.intersection(lemmas)
            if matched_keywords:
                return False, f"Potential injection detected (Keywords: {', '.join(matched_keywords)})"
                
            # Check for suspicious intent patterns (action verb + sensitive object)
            matched_verbs = self.action_verbs.intersection(lemmas)
            matched_objects = self.sensitive_objects.intersection(lemmas)
            
            if matched_verbs and matched_objects:
                return False, f"Suspicious intent detected (Actions: {', '.join(matched_verbs)}, Objects: {', '.join(matched_objects)})"
                
            # Advanced: Check for verb-object relationships in dependency parse
            for token in doc:
                # If token is a verb we're concerned about
                if token.lemma_ in self.action_verbs:
                    # Check its direct objects
                    for child in token.children:
                        if child.dep_ in ("dobj", "pobj") and child.lemma_ in self.sensitive_objects:
                            return False, f"Suspicious command structure detected: '{token.text} {child.text}'"
        
        except Exception as e:
            # Fallback if NLP processing fails
            print(f"NLP processing error: {e}")
            # Continue with other checks
                
        # --- Layer 3: Heuristic Checks ---
        # Check for excessive special characters
        special_char_count = sum(1 for c in input_text if not c.isalnum() and not c.isspace())
        if len(input_text) > 0 and special_char_count / len(input_text) > self.max_special_char_ratio:
            return False, "Suspicious pattern: excessive special characters"
            
        # Check for excessive length
        if len(input_text) > self.max_input_length:
            return False, "Input exceeds maximum allowed length"
            
        return True, None
        
    def process_output(self, output_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Process output text to detect potential prompt injection leakage.
        
        Args:
            output_text: The text to check for prompt injection leakage
            
        Returns:
            Tuple of (is_safe, reason, sanitized_output) where:
                - is_safe: Boolean indicating if the output is safe
                - reason: If not safe, the reason for rejection, otherwise None
                - sanitized_output: If not safe but can be sanitized, the sanitized output
        """
        # Similar checks as process_input, but focused on output-specific concerns
        if not output_text or not isinstance(output_text, str):
            return False, "Output must be a non-empty string", None
            
        # For outputs, we focus more on regex patterns that might indicate leakage
        for pattern in self.injection_patterns:
            if pattern.search(output_text):
                # For output, we might want to sanitize rather than reject
                sanitized = pattern.sub("[FILTERED]", output_text)
                return False, f"Potential prompt injection detected in output", sanitized
                
        return True, None, output_text