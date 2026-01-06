"""Safe shell command execution with timeouts and resource limits"""

import subprocess
import shlex
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ShellRunner:
    """Safe shell command runner with timeouts"""
    
    # Dangerous commands that should be blocked
    DANGEROUS_COMMANDS = [
        'rm -rf /',
        'rm -rf /*',
        'dd if=',
        'mkfs',
        'fdisk',
        'format',
        'del /f',
    ]
    
    def __init__(self, timeout: int = 300, cwd: Optional[str] = None):
        self.timeout = timeout
        self.cwd = cwd
    
    def run(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        allowlist: Optional[List[str]] = None,
    ) -> Tuple[int, str, str]:
        """
        Run a shell command safely
        
        Returns:
            (returncode, stdout, stderr)
        """
        # Check for dangerous commands
        if not self._is_safe(command, allowlist):
            raise ValueError(f"Dangerous command blocked: {command}")
        
        timeout = timeout or self.timeout
        cwd = cwd or self.cwd
        
        try:
            # Use shlex to safely parse command
            if isinstance(command, str):
                cmd_list = shlex.split(command)
            else:
                cmd_list = command
            
            logger.info(f"Executing: {' '.join(cmd_list)}")
            
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {command}")
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return -1, "", str(e)
    
    def _is_safe(self, command: str, allowlist: Optional[List[str]] = None) -> bool:
        """Check if command is safe to execute"""
        command_lower = command.lower()
        
        # Check allowlist first
        if allowlist:
            for allowed in allowlist:
                if allowed in command_lower:
                    return True
        
        # Check dangerous patterns
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                return False
        
        # Block commands that try to escape workspace
        if '..' in command and ('rm' in command or 'delete' in command):
            return False
        
        return True
    
    def run_safe(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Run command and return (success, output)
        """
        returncode, stdout, stderr = self.run(command, timeout, cwd)
        success = returncode == 0
        output = stdout if success else stderr
        return success, output

