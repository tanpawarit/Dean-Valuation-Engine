from typing import Optional, Tuple, cast
from src.guardrails.prompt_injection import PromptInjectionGuardrail
from src.guardrails.sensitive_info import SensitiveInfoGuardrail
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GuardrailManager:
    """
    Manager class that coordinates multiple guardrails and provides a unified interface.
    """
    
    def __init__(self) -> None:
        """Initialize the guardrail manager with all available guardrails."""
        self.prompt_injection_guardrail = PromptInjectionGuardrail()
        self.sensitive_info_guardrail = SensitiveInfoGuardrail()
        
    def validate_input(self, input_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate input text against all guardrails.
        
        Args:
            input_text: The text to validate
            
        Returns:
            Tuple containing:
                - Boolean indicating if the input is safe
                - Processed input text (sanitized/redacted if needed)
                - Error message if input is unsafe, None otherwise
        """
        # Check for prompt injection
        is_safe, error_message = self.prompt_injection_guardrail.process_input(input_text)
        if not is_safe:
            logger.warning(f"Prompt injection detected: {error_message}")
            # ในเวอร์ชันใหม่ไม่มี sanitized_input แล้ว ใช้ input_text เดิมแทน จะได้ส่งไป error node จบๆไปเลย
            return False, input_text, error_message
            
        # Check for sensitive information in input
        sensitive_result = self.sensitive_info_guardrail.process_input(input_text)
        if sensitive_result["has_sensitive_info"]:
            findings = sensitive_result["findings"]
            if isinstance(findings, list):
                logger.warning(f"Sensitive information detected in input. Findings: {len(findings)}")
            else:
                logger.warning("Sensitive information detected in input.")
            redacted = cast(str, sensitive_result["redacted_input"])
            return True, redacted, "Input contained sensitive information that was redacted"
            
        # Input passed all guardrails
        return True, input_text, None
        
    def process_output(self, output_text: str) -> str:
        """
        Process output text through all relevant guardrails.
        
        Args:
            output_text: The text to process
            
        Returns:
            Processed output text with any sensitive information redacted
        """ 
        is_safe, reason, sanitized_output = self.prompt_injection_guardrail.process_output(output_text)
        if not is_safe:
            logger.warning(f"Prompt injection detected in output: {reason}")
            output_text = sanitized_output if sanitized_output else output_text
            
        # Check for sensitive information in output
        sensitive_result = self.sensitive_info_guardrail.process_output(output_text)
        if sensitive_result["has_sensitive_info"]:
            findings = sensitive_result["findings"]
            if isinstance(findings, list):
                logger.warning(f"Sensitive information detected in output. Findings: {len(findings)}")
            else:
                logger.warning("Sensitive information detected in output.")
            return cast(str, sensitive_result["redacted_output"])
            
        # Output passed all guardrails
        return output_text
         