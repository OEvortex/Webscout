"""
ZeroArt Base: Core classes and utilities for ASCII art generation
"""

from typing import Dict, List, Optional


class ZeroArtFont:
    """Base class for ASCII art fonts"""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.letters: Dict[str, List[str]] = {}
        self.special_chars: Dict[str, List[str]] = {}

    def add_letter(self, char: str, art_lines: List[str]) -> None:
        """
        Add a custom letter to the font

        :param char: Character to add
        :param art_lines: List of art lines representing the character
        """
        self.letters[char.upper()] = art_lines

    def add_special_char(self, name: str, art_lines: List[str]) -> None:
        """
        Add a special ASCII art character or design

        :param name: Name of the special character
        :param art_lines: List of art lines representing the character
        """
        self.special_chars[name] = art_lines

    def get_letter(self, char: str) -> List[str]:
        """
        Get ASCII art for a specific character

        :param char: Character to retrieve
        :return: List of art lines or default space
        """
        return self.letters.get(char.upper(), self.letters.get(" ", [" "]))

    def render(self, text: str) -> str:
        """
        Render text as ASCII art

        :param text: Text to render as ASCII art
        :return: ASCII art representation of text
        """
        if not text:
            return ""

        # Get maximum height of any character in font
        max_height: int = max(len(self.get_letter(c)) for c in text)

        # Initialize art_lines with empty strings
        art_lines: List[str] = ["" for _ in range(max_height)]

        # Process each character
        for char in text:
            char_art: List[str] = self.get_letter(char)
            # Pad shorter characters with empty lines to match max_height
            while len(char_art) < max_height:
                char_art.append(" " * len(char_art[0]))

            # Add character art to each line
            for i in range(max_height):
                art_lines[i] += char_art[i] + " "

        return "\n".join(art_lines)
