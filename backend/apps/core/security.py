"""
Security utilities for file uploads and input validation
"""
import json
import re
from typing import Dict, Any, Tuple
from django.core.exceptions import ValidationError


class FileUploadValidator:
    """
    Validates .recip file uploads to prevent malicious content
    """
    
    # Maximum file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = ['.recip', '.json']
    
    # Maximum depth for nested JSON to prevent DoS
    MAX_JSON_DEPTH = 10
    
    # Maximum number of ingredients/steps to prevent memory issues
    MAX_INGREDIENTS = 200
    MAX_STEPS = 100
    
    # Maximum string lengths
    MAX_STRING_LENGTH = 10000
    MAX_ARRAY_LENGTH = 500
    
    @classmethod
    def validate_file(cls, uploaded_file) -> Tuple[bool, str, Dict]:
        """
        Validate uploaded .recip file
        
        Returns:
            (is_valid, error_message, parsed_data)
        """
        
        # 1. Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {cls.MAX_FILE_SIZE / 1024 / 1024}MB", {}
        
        # 2. Check file extension
        file_name = uploaded_file.name.lower()
        if not any(file_name.endswith(ext) for ext in cls.ALLOWED_EXTENSIONS):
            return False, "Invalid file type. Only .recip and .json files are allowed", {}
        
        # 3. Try to parse as JSON
        try:
            content = uploaded_file.read()
            
            # Check for null bytes (potential binary/malware)
            if b'\x00' in content:
                return False, "File contains invalid characters", {}
            
            # Decode and parse JSON
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "File must be valid UTF-8 text", {}
            
            # Parse JSON
            try:
                data = json.loads(text_content)
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {str(e)}", {}
            
            # Reset file pointer for later use
            uploaded_file.seek(0)
            
        except Exception as e:
            return False, f"Failed to read file: {str(e)}", {}
        
        # 4. Validate JSON structure
        is_valid, error = cls._validate_rcip_structure(data)
        if not is_valid:
            return False, error, {}
        
        # 5. Sanitize content
        sanitized_data = cls._sanitize_rcip_data(data)
        
        return True, "", sanitized_data
    
    @classmethod
    def _validate_rcip_structure(cls, data: Any, depth: int = 0) -> Tuple[bool, str]:
        """
        Validate RCIP JSON structure and check for malicious patterns
        """
        
        # Check JSON depth to prevent DoS
        if depth > cls.MAX_JSON_DEPTH:
            return False, "JSON structure too deeply nested"
        
        if not isinstance(data, dict):
            return False, "RCIP file must be a JSON object"
        
        # Check for required RCIP fields
        if 'meta' not in data and 'name' not in data:
            return False, "Invalid RCIP format: missing 'meta' or 'name' field"
        
        # Validate array sizes
        if 'ingredients' in data:
            if not isinstance(data['ingredients'], list):
                return False, "Ingredients must be an array"
            if len(data['ingredients']) > cls.MAX_INGREDIENTS:
                return False, f"Too many ingredients (max {cls.MAX_INGREDIENTS})"
        
        if 'steps' in data:
            if not isinstance(data['steps'], list):
                return False, "Steps must be an array"
            if len(data['steps']) > cls.MAX_STEPS:
                return False, f"Too many steps (max {cls.MAX_STEPS})"
        
        # Check string lengths
        for key, value in data.items():
            if isinstance(value, str) and len(value) > cls.MAX_STRING_LENGTH:
                return False, f"Field '{key}' is too long (max {cls.MAX_STRING_LENGTH} characters)"
            elif isinstance(value, list) and len(value) > cls.MAX_ARRAY_LENGTH:
                return False, f"Array '{key}' is too long (max {cls.MAX_ARRAY_LENGTH} items)"
            elif isinstance(value, dict):
                # Recursively validate nested objects
                is_valid, error = cls._validate_rcip_structure(value, depth + 1)
                if not is_valid:
                    return False, error
        
        # Check for suspicious patterns
        content_str = json.dumps(data)
        
        # Check for script tags (XSS attempt)
        if re.search(r'<script[\s>]', content_str, re.IGNORECASE):
            return False, "File contains potentially malicious content (script tags)"
        
        # Check for eval/exec patterns
        if re.search(r'\beval\s*\(|\bexec\s*\(', content_str, re.IGNORECASE):
            return False, "File contains potentially malicious content (code execution)"
        
        return True, ""
    
    @classmethod
    def _sanitize_rcip_data(cls, data: Dict) -> Dict:
        """
        Sanitize RCIP data by removing/escaping potentially dangerous content
        """
        
        def sanitize_value(value):
            if isinstance(value, str):
                # Remove null bytes
                value = value.replace('\x00', '')
                # Limit length
                if len(value) > cls.MAX_STRING_LENGTH:
                    value = value[:cls.MAX_STRING_LENGTH]
                # Remove script tags
                value = re.sub(r'<script[\s>].*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                return value
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value[:cls.MAX_ARRAY_LENGTH]]
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            else:
                return value
        
        return sanitize_value(data)


class AIInputValidator:
    """
    Validates and sanitizes AI input fields
    """
    
    # Maximum input lengths
    MAX_SHORT_INPUT = 500      # For search queries
    MAX_LONG_INPUT = 2000      # For descriptions/instructions
    MAX_LIST_INPUT = 5000      # For bulk lists (e.g., shopping list AI)
    
    # Minimum input length
    MIN_INPUT_LENGTH = 1
    
    # Patterns to block (SQL injection, command injection, etc.)
    BLOCKED_PATTERNS = [
        r';\s*DROP\s+TABLE',
        r';\s*DELETE\s+FROM',
        r';\s*INSERT\s+INTO',
        r';\s*UPDATE\s+.*\s+SET',
        r'UNION\s+SELECT',
        r'<script[\s>]',
        r'javascript:',
        r'onerror\s*=',
        r'onclick\s*=',
        r'\$\(.*\)',  # jQuery selectors
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess',
        r'os\.system',
    ]
    
    @classmethod
    def validate_search_input(cls, text: str, field_name: str = "input") -> Tuple[bool, str, str]:
        """
        Validate search/query input
        
        Returns:
            (is_valid, error_message, sanitized_text)
        """
        return cls._validate_input(text, cls.MAX_SHORT_INPUT, field_name)
    
    @classmethod
    def validate_description_input(cls, text: str, field_name: str = "description") -> Tuple[bool, str, str]:
        """
        Validate longer description/instruction input
        
        Returns:
            (is_valid, error_message, sanitized_text)
        """
        return cls._validate_input(text, cls.MAX_LONG_INPUT, field_name)
    
    @classmethod
    def validate_list_input(cls, text: str, field_name: str = "list") -> Tuple[bool, str, str]:
        """
        Validate bulk list input (e.g., shopping list AI)
        
        Returns:
            (is_valid, error_message, sanitized_text)
        """
        return cls._validate_input(text, cls.MAX_LIST_INPUT, field_name)
    
    @classmethod
    def _validate_input(cls, text: str, max_length: int, field_name: str) -> Tuple[bool, str, str]:
        """
        Core validation logic
        """
        
        # Check if text is string
        if not isinstance(text, str):
            return False, f"{field_name} must be text", ""
        
        # Check length
        if len(text) < cls.MIN_INPUT_LENGTH:
            return False, f"{field_name} is too short", ""
        
        if len(text) > max_length:
            return False, f"{field_name} is too long (max {max_length} characters)", ""
        
        # Check for null bytes
        if '\x00' in text:
            return False, f"{field_name} contains invalid characters", ""
        
        # Check for blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"{field_name} contains potentially malicious content", ""
        
        # Check for excessive special characters (potential encoding attack)
        special_char_count = len(re.findall(r'[^\w\s\-.,;:!?\'"()]', text))
        if special_char_count > len(text) * 0.3:  # More than 30% special chars
            return False, f"{field_name} contains too many special characters", ""
        
        # Sanitize
        sanitized = cls._sanitize_text(text)
        
        return True, "", sanitized
    
    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        """
        Sanitize text input
        """
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove potential XSS patterns
        text = re.sub(r'<script[\s>].*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'onerror\s*=', '', text, flags=re.IGNORECASE)
        text = re.sub(r'onclick\s*=', '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text



