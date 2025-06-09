"""
Prompt Injection Guardrail

This module provides protection against prompt injection attacks by detecting and
filtering potentially malicious input patterns.
"""

import re
from typing import Dict, List, Optional, Tuple, Union


class PromptInjectionGuardrail:
    """
    A guardrail to detect and prevent prompt injection attacks.
    
    This class implements pattern matching and heuristic detection to identify
    common prompt injection techniques without relying on external libraries.
    """
    
    def __init__(self) -> None:
        """Initialize the prompt injection guardrail with detection patterns."""
        # Common prompt injection patterns
        self.injection_patterns: List[str] = [
            # System prompt leakage attempts
            r"ignore previous instructions",
            r"disregard (all|previous|your) instructions",
            r"forget (all|previous|your) instructions",
            r"ignore (all|previous|your) constraints",
            r"system prompt",
            r"you are now",
            r"your new role is",
            r"act as",
            r"pretend to be",
            r"you're no longer",
            
            # Delimiter attacks
            r"<\s*system\s*>",
            r"<\s*\/system\s*>",
            r"<\s*user\s*>",
            r"<\s*\/user\s*>",
            r"<\s*assistant\s*>",
            r"<\s*\/assistant\s*>",
            r"\[\s*system\s*\]",
            r"\[\s*\/system\s*\]",
            
            # Jailbreak attempts
            r"DAN",  # Do Anything Now
            r"STAN",  # Strive To Avoid Norms
            r"jailbreak",
            r"dev mode",
            r"developer mode",
            r"sudo mode",
            r"admin mode",
            r"root mode",
            
            # Command injection
            r"print\(\s*\".*\"\s*\)",
            r"exec\(\s*\".*\"\s*\)",
            r"eval\(\s*\".*\"\s*\)",
            r"os\.(system|popen|exec)",
            r"subprocess\.(call|run|Popen)",
        ]
        
        # Compile all patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.injection_patterns]
        
    def validate(self, input_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input text against prompt injection patterns.
        
        Args:
            input_text: The text to validate
            
        Returns:
            Tuple containing:
                - Boolean indicating if the input is safe (True) or potentially harmful (False)
                - Optional error message explaining the rejection reason if unsafe
        """
        if not input_text or not isinstance(input_text, str):
            return False, "Input must be a non-empty string"
            
        # Check for injection patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(input_text):
                return False, f"Potential prompt injection detected: {self.injection_patterns[i]}"
                
        # Check for excessive special characters that might be used to confuse models
        special_char_ratio = sum(1 for c in input_text if not c.isalnum() and not c.isspace()) / max(len(input_text), 1)
        if special_char_ratio > 0.3:  # If more than 30% are special characters
            return False, "Suspicious pattern: excessive special characters"
            
        # Check for very long inputs that might be trying to overwhelm the model
        if len(input_text) > 10000:  # Arbitrary limit, adjust as needed
            return False, "Input exceeds maximum allowed length"
            
        return True, None
        
    def sanitize(self, input_text: str) -> str:
        """
        Sanitize input by removing or replacing potentially harmful patterns.
        
        Args:
            input_text: The text to sanitize
            
        Returns:
            Sanitized version of the input text
        """
        sanitized = input_text
        
        # Replace common injection patterns with safe alternatives
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub("[FILTERED]", sanitized)
            
        return sanitized
        
    def process_input(self, input_text: str) -> Dict[str, Union[str, bool, Optional[str]]]:
        """
        Process input text through the guardrail.
        
        Args:
            input_text: The text to process
            
        Returns:
            Dictionary containing:
                - 'is_safe': Boolean indicating if input is safe
                - 'sanitized_input': Sanitized version of the input
                - 'original_input': Original input text
                - 'error_message': Error message if input is unsafe, None otherwise
        """
        is_safe, error_message = self.validate(input_text)
        sanitized_input = self.sanitize(input_text) if not is_safe else input_text
        
        return {
            "is_safe": is_safe,
            "sanitized_input": sanitized_input,
            "original_input": input_text,
            "error_message": error_message
        }
