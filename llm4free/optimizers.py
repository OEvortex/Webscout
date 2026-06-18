"""Prompt optimization utilities."""

import os
import platform
import subprocess
from typing import Optional


class Optimizers:
    """
    >>> Optimizers.coder("write a hello world")
    Returns optimized prompt for code generation
    """

    @staticmethod
    def coder(prompt: str) -> str:
        """Unified optimizer for both code and shell commands."""
        # Get system info for shell commands
        operating_system: str = ""
        if platform.system() == "Windows":
            operating_system = "Windows"
        elif platform.system() == "Darwin":
            operating_system = "MacOS"
        elif platform.system() == "Linux":
            try:
                result: str = subprocess.check_output(["lsb_release", "-si"]).decode().strip()
                operating_system = f"Linux/{result}" if result else "Linux"
            except Exception:
                operating_system = "Linux"
        else:
            operating_system = platform.system()

        # Get shell info
        shell_name: str = "/bin/sh"
        if platform.system() == "Windows":
            shell_name = "powershell.exe" if os.getenv("PSModulePath") else "cmd.exe"
        else:
            shell_env: Optional[str] = os.getenv("SHELL")
            if shell_env:
                shell_name = shell_env

        return (
            f"""<system_context>
<role>
  Your Role: You are a code generation expert. Analyze the request and provide appropriate output.
  If the request starts with '!' or involves system/shell operations, provide a shell command.
  Otherwise, provide Python code.
</role>
<rules>
   RULES:
     - Provide ONLY code/command output without any description or markdown
     - For shell commands:
         - Target OS: {operating_system}
         - Shell: {shell_name}
         - Combine multiple steps when possible
         - Use appropriate flags for safety and clarity
     - For Python code:
        - Include necessary imports
        - Handle errors appropriately
        - Follow PEP 8 style
        - Use type hints where appropriate
        - Include docstrings for functions
     - If details are missing, use most logical implementation
     - No warnings, descriptions, or explanations
     - For complex tasks, break down into smaller logical steps
</rules>
<request>
     Request: {prompt}
</request>
<output>
    Output:
</output>
</system_context>"""
        )
