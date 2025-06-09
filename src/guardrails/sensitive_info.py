"""
Sensitive Information Guardrail

This module provides protection against leakage of sensitive information in both
input and output text by detecting and redacting patterns that match common
sensitive data formats.
"""

import re
from typing import Dict, List, Optional, Pattern, Set, Tuple, Union


class SensitiveInfoGuardrail:
    """
    A guardrail to detect and redact sensitive information.
    
    This class implements pattern matching to identify common sensitive data patterns
    such as credit card numbers, social security numbers, API keys, etc.
    """
    
    def __init__(self) -> None:
        """Initialize the sensitive information guardrail with detection patterns."""
        # Define patterns for different types of sensitive information
        self.patterns: Dict[str, Pattern[str]] = {
            # Credit card numbers (major card formats)
            "credit_card": re.compile(
                r"(?:\d{4}[-\s]?){3}\d{4}|"  # 16 digits with optional separators
                r"\d{4}\s\d{6}\s\d{5}|"      # AMEX format
                r"\d{4}-\d{4}-\d{4}-\d{4}"   # Dashed format
            ),
            
            # Social Security Numbers (US)
            "ssn": re.compile(r"\d{3}[-\s]?\d{2}[-\s]?\d{4}"),
            
            # Phone numbers (international formats)
            "phone": re.compile(
                r"(?:\+\d{1,3}[-\s]?)?(?:\(\d{1,4}\)|\d{1,4})[-\s]?\d{3,4}[-\s]?\d{3,4}"
            ),
            
            # Email addresses
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            
            # API keys and tokens (common patterns)
            "api_key": re.compile(
                r"(?:api[_-]?key|token|secret|password|pwd|auth)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{20,})['\"]?"
            ),
            
            # IP addresses
            "ip_address": re.compile(
                r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
            ),
            
            # Thai national ID
            "thai_id": re.compile(r"\d{1,2}[-\s]?\d{4}[-\s]?\d{5}[-\s]?\d{2}[-\s]?\d{1}"),
            
            # Passport numbers (generic pattern)
            "passport": re.compile(r"[A-Z]{1,2}\d{6,9}|[A-Z]{1,2}[-\s]?\d{6,9}"),
            
            # URLs with authentication credentials
            "auth_url": re.compile(
                r"(?:https?:\/\/)(?:[^:@\/\n]+):(?:[^:@\/\n]+)@"
            ),
            
            # AWS access keys
            "aws_key": re.compile(r"(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
            
            # Private keys
            "private_key": re.compile(
                r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----"
            ),
        }
        
        # Words that might indicate sensitive context
        self.sensitive_keywords: Set[str] = {
            "password", "secret", "token", "key", "credential", "auth", 
            "private", "confidential", "sensitive", "restricted", "personal",
            "ssn", "social security", "credit card", "cvv", "expiration", 
            "passport", "license", "id number", "account", "routing", "swift",
            "username", "login", "pwd", "passcode", "pin", "access code"
        }
        
    def _check_luhn(self, card_number: str) -> bool:
        """
        Validate a credit card number using the Luhn algorithm.
        
        Args:
            card_number: The credit card number to validate
            
        Returns:
            Boolean indicating if the card number passes Luhn check
        """
        # Remove any non-digit characters
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:  # Most cards are between 13-19 digits
            return False
            
        # Apply Luhn algorithm
        check_sum = 0
        num_digits = len(digits)
        odd_even = num_digits & 1
        
        for i in range(num_digits):
            digit = digits[i]
            if ((i & 1) ^ odd_even) == 0:
                digit *= 2
                if digit > 9:
                    digit -= 9
            check_sum += digit
            
        return (check_sum % 10) == 0
        
    def detect_sensitive_info(self, text: str) -> List[Dict[str, Union[str, int, int]]]:
        """
        Detect sensitive information in the provided text.
        
        Args:
            text: The text to scan for sensitive information
            
        Returns:
            List of dictionaries containing details about detected sensitive information:
                - 'type': Type of sensitive information detected
                - 'start': Start position in the text
                - 'end': End position in the text
                - 'value': The detected sensitive information
        """
        if not text or not isinstance(text, str):
            return []
            
        findings: List[Dict[str, Union[str, int, int]]] = []
        
        # Check for each pattern
        for info_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                # For credit cards, apply additional validation
                if info_type == "credit_card":
                    card_num = ''.join(c for c in match.group(0) if c.isdigit())
                    if not self._check_luhn(card_num):
                        continue
                        
                findings.append({
                    "type": info_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(0)
                })
                
        # Check for sensitive keywords in context
        for keyword in self.sensitive_keywords:
            keyword_pattern = re.compile(
                r"(?i)" + re.escape(keyword) + r"\s*[:=]\s*([^\s,;]{8,})"
            )
            for match in keyword_pattern.finditer(text):
                findings.append({
                    "type": "sensitive_keyword",
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(0)
                })
                
        return findings
        
    def redact_text(self, text: str) -> str:
        """
        Redact sensitive information from the provided text.
        
        Args:
            text: The text to redact
            
        Returns:
            Text with sensitive information redacted
        """
        if not text or not isinstance(text, str):
            return text
            
        # Get all findings
        findings = self.detect_sensitive_info(text)
        
        # Sort findings by start position in reverse order to avoid
        # changing string positions when replacing
        findings.sort(key=lambda x: x["start"], reverse=True)
        
        # Create a new string with redactions
        redacted_text = text
        for finding in findings:
            info_type = finding["type"]
            start = finding["start"]
            end = finding["end"]
            value = str(finding["value"])  # Ensure value is a string
            
            # Create appropriate redaction based on the type
            if info_type == "email":
                # Keep domain part visible
                parts = value.split('@')
                if len(parts) == 2:
                    redaction = f"[REDACTED_EMAIL]@{parts[1]}"
                else:
                    redaction = "[REDACTED_EMAIL]"
            elif info_type == "phone":
                # Keep last 4 digits if long enough
                digits = ''.join(c for c in value if c.isdigit())
                if len(digits) >= 4:
                    redaction = f"[REDACTED_PHONE_***{digits[-4:]}]"
                else:
                    redaction = "[REDACTED_PHONE]"
            elif info_type == "credit_card":
                # Keep last 4 digits
                digits = ''.join(c for c in value if c.isdigit())
                redaction = f"[REDACTED_CC_***{digits[-4:]}]"
            elif info_type == "ip_address":
                # Redact last octet
                parts = value.split('.')
                if len(parts) == 4:
                    redaction = f"{parts[0]}.{parts[1]}.{parts[2]}.[REDACTED]"
                else:
                    redaction = "[REDACTED_IP]"
            else:
                # Generic redaction
                redaction = f"[REDACTED_{str(info_type).upper()}]"
                
            # Replace the sensitive information with the redaction
            redacted_text = redacted_text[:start] + redaction + redacted_text[end:]
            
        return redacted_text
        
    def process_input(self, input_text: str) -> Dict[str, Union[str, bool, List[Dict[str, Union[str, int]]]]]:
        """
        Process input text through the guardrail.
        
        Args:
            input_text: The text to process
            
        Returns:
            Dictionary containing:
                - 'has_sensitive_info': Boolean indicating if sensitive info was detected
                - 'redacted_input': Input with sensitive information redacted
                - 'original_input': Original input text
                - 'findings': List of sensitive information findings
        """
        findings = self.detect_sensitive_info(input_text)
        redacted_input = self.redact_text(input_text)
        
        return {
            "has_sensitive_info": len(findings) > 0,
            "redacted_input": redacted_input,
            "original_input": input_text,
            "findings": findings
        }
        
    def process_output(self, output_text: str) -> Dict[str, Union[str, bool, List[Dict[str, Union[str, int]]]]]:
        """
        Process output text through the guardrail.
        
        Args:
            output_text: The text to process
            
        Returns:
            Dictionary containing:
                - 'has_sensitive_info': Boolean indicating if sensitive info was detected
                - 'redacted_output': Output with sensitive information redacted
                - 'original_output': Original output text
                - 'findings': List of sensitive information findings
        """
        findings = self.detect_sensitive_info(output_text)
        redacted_output = self.redact_text(output_text)
        
        return {
            "has_sensitive_info": len(findings) > 0,
            "redacted_output": redacted_output,
            "original_output": output_text,
            "findings": findings
        }
