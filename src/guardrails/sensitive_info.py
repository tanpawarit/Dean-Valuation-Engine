"""
Sensitive Information Guardrail

This module provides protection against leakage of sensitive information in both
input and output text by detecting and redacting patterns that match common
sensitive data formats. Uses both regex patterns and NLP-based detection.
"""

import re
import spacy
from functools import lru_cache
from typing import Dict, List, Pattern, Set, Union, Any

# Type definitions for spaCy
SpacyDoc = Any  # spacy.tokens.doc.Doc
SpacyToken = Any  # spacy.tokens.token.Token
SpacySpan = Any  # spacy.tokens.span.Span


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


class SensitiveInfoGuardrail:
    """
    A guardrail to detect and redact sensitive information.
    
    This class implements pattern matching and NLP-based techniques to identify 
    common sensitive data patterns such as credit card numbers, social security 
    numbers, API keys, etc. with enhanced contextual understanding.
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
        
        # NLP-based entity categories that might contain sensitive information
        self.sensitive_entity_types: Set[str] = {
            "PERSON",       # Names of people
            "ORG",         # Organizations
            "GPE",         # Geopolitical entities (countries, cities)
            "LOC",         # Non-GPE locations
            "MONEY",       # Monetary values
            "CARDINAL",    # Numbers
            "DATE",        # Dates
        }
        
        # Context words that when combined with entities might indicate sensitive info
        self.context_indicators: Dict[str, Set[str]] = {
            "personal": {"my", "your", "his", "her", "their", "our"},
            "credential": {"login", "password", "username", "credential", "account"},
            "financial": {"bank", "account", "credit", "debit", "card", "payment", "transaction"}
        }
        
        # Configuration for NLP processing
        self.use_nlp: bool = True
        self.confidence_threshold: float = 0.7  # Minimum confidence for NLP-based detection
        
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
        
    def detect_sensitive_info(self, text: str) -> List[Dict[str, Union[str, int, int, float]]]:
        """
        Detect sensitive information in the provided text using both regex patterns
        and NLP-based entity recognition.
        
        Args:
            text: The text to scan for sensitive information
            
        Returns:
            List of dictionaries containing details about detected sensitive information:
                - 'type': Type of sensitive information detected
                - 'start': Start position in the text
                - 'end': End position in the text
                - 'value': The detected sensitive information
                - 'confidence': Confidence score (for NLP-based detections)
        """
        if not text or not isinstance(text, str):
            return []
            
        findings: List[Dict[str, Union[str, int, int, float]]] = []
        
        # --- Layer 1: Pattern-based detection ---
        # Check for each regex pattern
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
                    "value": match.group(0),
                    "confidence": 1.0,  # Regex matches have 100% confidence
                    "method": "regex"
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
                    "value": match.group(0),
                    "confidence": 0.9,  # High confidence for keyword-value pairs
                    "method": "keyword"
                })
        
        # --- Layer 2: NLP-based detection ---
        if self.use_nlp and len(text) > 0:
            try:
                # Load the NLP model
                nlp = load_nlp_model()
                
                # Process the text with spaCy
                doc = nlp(text)
                
                # Check for named entities that might be sensitive
                for ent in doc.ents:
                    # If entity type is in our sensitive list
                    if ent.label_ in self.sensitive_entity_types:
                        # Calculate contextual confidence based on surrounding words
                        confidence = self._calculate_entity_confidence(ent, doc)
                        
                        if confidence >= self.confidence_threshold:
                            findings.append({
                                "type": f"entity_{ent.label_.lower()}",
                                "start": ent.start_char,
                                "end": ent.end_char,
                                "value": ent.text,
                                "confidence": confidence,
                                "method": "nlp"
                            })
                
                # Check for potential sensitive patterns using dependency parsing
                self._check_dependency_patterns(doc, findings)
                
            except Exception as e:
                # Fallback if NLP processing fails
                print(f"NLP processing error in sensitive info detection: {e}")
                # Continue with other checks
                
        return findings
    
    def _calculate_entity_confidence(self, entity: SpacySpan, doc: SpacyDoc) -> float:
        """
        Calculate confidence score for an entity based on surrounding context.
        
        Args:
            entity: The spaCy entity span
            doc: The full spaCy document
            
        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.5  # Start with neutral confidence
        
        # Get context (5 tokens before and after)
        start_idx = max(0, entity.start - 5)
        end_idx = min(len(doc), entity.end + 5)
        
        context_tokens = [token.text.lower() for token in doc[start_idx:end_idx]]
        
        # Check for personal context indicators
        for context_type, indicators in self.context_indicators.items():
            for indicator in indicators:
                if indicator in context_tokens:
                    base_confidence += 0.1  # Increase confidence for each indicator
        
        # Entity type specific adjustments
        if entity.label_ == "PERSON":
            # Names are often sensitive
            base_confidence += 0.1
            
            # Check if it looks like a full name (2+ tokens)
            if len(entity) >= 2:
                base_confidence += 0.1
                
        elif entity.label_ == "CARDINAL" and len(entity.text) >= 8:
            # Long numbers are more likely to be sensitive
            base_confidence += 0.1
            
        # Cap confidence at 1.0
        return min(base_confidence, 1.0)
    
    def _check_dependency_patterns(self, doc: SpacyDoc, findings: List[Dict[str, Any]]) -> None:
        """
        Check for sensitive information using dependency parsing patterns.
        
        Args:
            doc: The spaCy document
            findings: List to append findings to
        """
        # Pattern: possessive + sensitive noun (e.g., "my password")
        for token in doc:
            if token.dep_ in ("poss", "nmod") and token.head.text.lower() in self.sensitive_keywords:
                # Found pattern like "my password", now look for values
                for child in token.head.children:
                    if child.dep_ in ("amod", "compound", "nummod") or child.pos_ == "NUM":
                        start = min(token.idx, token.head.idx, child.idx)
                        end = max(token.idx + len(token.text), 
                                 token.head.idx + len(token.head.text),
                                 child.idx + len(child.text))
                        
                        findings.append({
                            "type": "sensitive_phrase",
                            "start": start,
                            "end": end,
                            "value": doc.text[start:end],
                            "confidence": 0.8,
                            "method": "dependency"
                        })
        
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
        
    def process_input(self, input_text: str) -> Dict[str, Union[str, bool, List[Dict[str, Union[str, int, int, float]]]]]:
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
        
    def process_output(self, output_text: str) -> Dict[str, Union[str, bool, List[Dict[str, Union[str, int, int, float]]]]]:
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
