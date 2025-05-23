"""
ZeroArt Effects: ASCII art text effects and transformations
"""

import random
import textwrap
from typing import List, Optional, Union
from .base import ZeroArtFont
 
class AsciiArtEffects:
    """Collection of ASCII art text effects"""
    
    @staticmethod
    def rainbow_effect(text: str, font: ZeroArtFont) -> str:
        """
        Apply a rainbow-like color effect to ASCII art
        
        :param text: Text to render
        :param font: Font to use
        :return: Rainbow-styled ASCII art
        """
        colors: List[str] = [
            '\033[91m',  # Red
            '\033[93m',  # Yellow
            '\033[92m',  # Green
            '\033[94m',  # Blue
            '\033[95m',  # Magenta
        ]
        
        art: str = font.render(text)
        art_lines: List[str] = art.split('\n')
        
        colored_lines: List[str] = []
        for line in art_lines:
            colored_line: str = ''
            for char in line:
                color: str = random.choice(colors)
                colored_line += color + char
            colored_lines.append(colored_line + '\033[0m')  # Reset color
        
        return '\n'.join(colored_lines)
    
    @staticmethod
    def glitch_effect(text: str, font: ZeroArtFont, glitch_intensity: float = 0.1) -> str:
        """
        Apply a glitch-like distortion to ASCII art
        
        :param text: Text to render
        :param font: Font to use
        :param glitch_intensity: Probability of character distortion
        :return: Glitched ASCII art
        """
        art: str = font.render(text)
        art_lines: List[str] = art.split('\n')
        
        glitched_lines: List[str] = []
        glitch_chars: List[str] = ['~', '^', '`', '¯', '±']
        
        for line in art_lines:
            glitched_line: str = ''
            for char in line:
                if random.random() < glitch_intensity:
                    glitched_line += random.choice(glitch_chars)
                else:
                    glitched_line += char
            glitched_lines.append(glitched_line)
        
        return '\n'.join(glitched_lines)

    @staticmethod
    def wrap_text(text: str, width: int = 20) -> str:
        """
        Wrap ASCII art text to a specific width
        
        :param text: Text to wrap
        :param width: Maximum line width
        :return: Wrapped text
        """
        return textwrap.fill(text, width=width)

    @staticmethod
    def outline_effect(text: str, font: ZeroArtFont, outline_char: str = '*') -> str:
        """
        Add an outline effect to ASCII art
        
        :param text: Text to render
        :param font: Font to use
        :param outline_char: Character to use for outline
        :return: ASCII art with outline
        """
        art: str = font.render(text)
        art_lines: List[str] = art.split('\n')
        
        outlined_lines: List[str] = []
        for line in art_lines:
            outlined_line: str = outline_char + line + outline_char
            outlined_lines.append(outlined_line)
        
        top_bottom_line: str = outline_char * (len(outlined_lines[0]))
        
        return '\n'.join([top_bottom_line] + outlined_lines + [top_bottom_line])