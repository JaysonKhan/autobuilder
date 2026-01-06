"""Sensitive data redaction utilities"""

import re
from typing import List, Optional


class Redactor:
    """Redacts sensitive information from text"""
    
    def __init__(self, patterns: Optional[List[str]] = None):
        self.patterns = patterns or [
            r'DB_PASSWORD\s*=\s*[^\s\n]+',
            r'TOKEN\s*=\s*[^\s\n]+',
            r'Authorization:\s*[^\s\n]+',
            r'password\s*=\s*[^\s\n]+',
            r'secret\s*=\s*[^\s\n]+',
            r'api_key\s*=\s*[^\s\n]+',
            r'-----BEGIN\s+[A-Z\s]+-----[\s\S]*?-----END\s+[A-Z\s]+-----',  # Private keys
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
    
    def redact(self, text: str) -> str:
        """Redact sensitive patterns from text"""
        if not text:
            return text
        
        result = text
        for pattern in self.compiled_patterns:
            result = pattern.sub(self._replace_match, result)
        
        return result
    
    def _replace_match(self, match: re.Match) -> str:
        """Replace matched pattern with redacted version"""
        matched = match.group(0)
        # Try to preserve structure
        if '=' in matched:
            key = matched.split('=')[0].strip()
            return f"{key}=***REDACTED***"
        elif ':' in matched:
            key = matched.split(':')[0].strip()
            return f"{key}: ***REDACTED***"
        else:
            return "***REDACTED***"
    
    def redact_file(self, filepath: str) -> str:
        """Read file and redact sensitive content"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return self.redact(content)
        except Exception as e:
            return f"Error reading file: {e}"


def get_redactor(config: dict) -> Redactor:
    """Get redactor instance from config"""
    patterns = config.get('security', {}).get('redact_patterns', [])
    return Redactor(patterns)

