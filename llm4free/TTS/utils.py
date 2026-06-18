"""
Text processing utilities for TTS providers.
"""
import re
from typing import Dict, List, Optional, Pattern, Set, Tuple, Union, cast


class SentenceTokenizer:
    """Advanced sentence tokenizer with support for complex cases and proper formatting."""

    def __init__(self) -> None:
        # Common abbreviations by category
        self.TITLES: Set[str] = {
            'mr', 'mrs', 'ms', 'dr', 'prof', 'rev', 'sr', 'jr', 'esq',
            'hon', 'pres', 'gov', 'atty', 'supt', 'det', 'rev', 'col','maj', 'gen', 'capt', 'cmdr',
            'lt', 'sgt', 'cpl', 'pvt'
        }

        self.ACADEMIC: Set[str] = {
            'ph.d', 'phd', 'm.d', 'md', 'b.a', 'ba', 'm.a', 'ma', 'd.d.s', 'dds',
            'm.b.a', 'mba', 'b.sc', 'bsc', 'm.sc', 'msc', 'llb', 'll.b', 'bl'
        }

        self.ORGANIZATIONS: Set[str] = {
            'inc', 'ltd', 'co', 'corp', 'llc', 'llp', 'assn', 'bros', 'plc', 'cos',
            'intl', 'dept', 'est', 'dist', 'mfg', 'div'
        }

        self.MONTHS: Set[str] = {
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        }

        self.UNITS: Set[str] = {
            'oz', 'pt', 'qt', 'gal', 'ml', 'cc', 'km', 'cm', 'mm', 'ft', 'in',
            'kg', 'lb', 'lbs', 'hz', 'khz', 'mhz', 'ghz', 'kb', 'mb', 'gb', 'tb'
        }

        self.TECHNOLOGY: Set[str] = {
            'v', 'ver', 'app', 'sys', 'dir', 'exe', 'lib', 'api', 'sdk', 'url',
            'cpu', 'gpu', 'ram', 'rom', 'hdd', 'ssd', 'lan', 'wan', 'sql', 'html'
        }

        self.MISC: Set[str] = {
            'vs', 'etc', 'ie', 'eg', 'no', 'al', 'ca', 'cf', 'pp', 'est', 'st',
            'approx', 'appt', 'apt', 'dept', 'depts', 'min', 'max', 'avg'
        }

        # Combine all abbreviations
        self.all_abbreviations: Set[str] = (
            self.TITLES | self.ACADEMIC | self.ORGANIZATIONS |
            self.MONTHS | self.UNITS | self.TECHNOLOGY | self.MISC
        )

        # Special patterns
        self.ELLIPSIS: str = r'\.{2,}|…'
        self.URL_PATTERN: str = (
            r'(?:https?:\/\/|www\.)[\w\-\.]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?'
        )
        self.EMAIL_PATTERN: str = r'[\w\.-]+@[\w\.-]+\.\w+'
        self.NUMBER_PATTERN: str = (
            r'\d+(?:\.\d+)?(?:%|°|km|cm|mm|m|kg|g|lb|ft|in|mph|kmh|hz|mhz|ghz)?'
        )

        # Quote and bracket pairs
        self.QUOTE_PAIRS: Dict[str, str] = {
            '"': '"', "'": "'", "「": "」", "『": "』",
            "«": "»", "‹": "›", "‚": "'"
        }

        self.BRACKETS: Dict[str, str] = {
            '(': ')', '[': ']', '{': '}', '⟨': '⟩', '「': '」',
            '『': '』', '【': '】', '〖': '〗', '｢': '｣'
        }

        # Compile regex patterns
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance."""
        # Pattern for finding potential sentence boundaries
        self.SENTENCE_END: Pattern = re.compile(
            r'''
            # Group for sentence endings
            (?:
                # Standard endings with optional quotes/brackets
                (?<=[.!?])[\"\'\)\]\}»›」』\s]*

                # Ellipsis
                |(?:\.{2,}|…)

                # Asian-style endings
                |(?<=[。！？」』】\s])
            )

            # Must be followed by whitespace and capital letter or number
            (?=\s+(?:[A-Z0-9]|["'({[\[「『《‹〈][A-Z]))
            ''',
            re.VERBOSE
        )

        # Pattern for abbreviations
        abbrev_pattern = '|'.join(re.escape(abbr) for abbr in self.all_abbreviations)
        self.ABBREV_PATTERN: Pattern = re.compile(
            fr'\b(?:{abbrev_pattern})\.?',
            re.IGNORECASE
        )

    def _protect_special_cases(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Protect URLs, emails, and other special cases from being split."""
        protected = text
        placeholders: Dict[str, str] = {}
        counter = 0

        # Protect URLs and emails
        for pattern in [self.URL_PATTERN, self.EMAIL_PATTERN]:
            for match in re.finditer(pattern, protected):
                placeholder = f'__PROTECTED_{counter}__'
                placeholders[placeholder] = match.group()
                protected = protected.replace(match.group(), placeholder)
                counter += 1

        # Protect quoted content
        stack = []
        protected_chars = list(protected)
        i = 0
        while i < len(protected_chars):
            char = protected_chars[i]
            if char in self.QUOTE_PAIRS:
                stack.append((char, i))
            elif stack and char == self.QUOTE_PAIRS[stack[-1][0]]:
                start_quote, start_idx = stack.pop()
                content = ''.join(protected_chars[start_idx:i + 1])
                placeholder = f'__PROTECTED_{counter}__'
                placeholders[placeholder] = content
                protected_chars[start_idx:i + 1] = list(placeholder)
                counter += 1
            i += 1

        return ''.join(protected_chars), placeholders

    def _restore_special_cases(self, text: str, placeholders: Dict[str, str]) -> str:
        """Restore protected content."""
        restored = text
        for placeholder, original in placeholders.items():
            restored = restored.replace(placeholder, original)
        return restored

    def _handle_abbreviations(self, text: str) -> str:
        """Handle abbreviations to prevent incorrect sentence splitting."""
        def replace_abbrev(match: re.Match) -> str:
            abbr = match.group().lower().rstrip('.')
            if abbr in self.all_abbreviations:
                return match.group().replace('.', '__DOT__')
            return match.group()

        return self.ABBREV_PATTERN.sub(replace_abbrev, text)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving paragraph breaks."""
        # Replace multiple newlines with special marker
        text = re.sub(r'\n\s*\n', ' __PARA__ ', text)
        # Normalize remaining whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _restore_formatting(self, sentences: List[str]) -> List[str]:
        """Restore original formatting and clean up sentences."""
        restored = []
        for sentence in sentences:
            # Restore dots in abbreviations
            sentence = sentence.replace('__DOT__', '.')

            # Restore paragraph breaks
            sentence = sentence.replace('__PARA__', '\n\n')

            # Clean up whitespace
            sentence = re.sub(r'\s+', ' ', sentence).strip()

            # Capitalize first letter if it's lowercase and not an abbreviation
            words = sentence.split()
            if words and words[0].lower() not in self.all_abbreviations:
                sentence = sentence[0].upper() + sentence[1:]

            if sentence:
                restored.append(sentence)

        return restored

    def tokenize(self, text: str) -> List[str]:
        """
        Split text into sentences while handling complex cases.

        Args:
            text (str): Input text to split into sentences.

        Returns:
            List[str]: List of properly formatted sentences.
        """
        if not text or not text.strip():
            return []

        # Step 1: Protect special cases
        protected_text, placeholders = self._protect_special_cases(text)

        # Step 2: Normalize whitespace
        protected_text = self._normalize_whitespace(protected_text)

        # Step 3: Handle abbreviations
        protected_text = self._handle_abbreviations(protected_text)

        # Step 4: Split into potential sentences
        potential_sentences = self.SENTENCE_END.split(protected_text)

        # Step 5: Process and restore formatting
        sentences = self._restore_formatting(potential_sentences)

        # Step 6: Restore special cases
        sentences = [self._restore_special_cases(s, placeholders) for s in sentences]

        # Step 7: Post-process sentences
        final_sentences = []
        current_sentence = []

        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                continue

            # Check if sentence might be continuation of previous
            if current_sentence and sentence[0].islower():
                current_sentence.append(sentence)
            else:
                if current_sentence:
                    final_sentences.append(' '.join(current_sentence))
                current_sentence = [sentence]

        # Add last sentence if exists
        if current_sentence:
            final_sentences.append(' '.join(current_sentence))

        return final_sentences


def split_sentences(text: str) -> List[str]:
    """
    Convenience function to split text into sentences using SentenceTokenizer.

    Args:
        text (str): Input text to split into sentences.

    Returns:
        List[str]: List of properly formatted sentences.
    """
    tokenizer = SentenceTokenizer()
    return tokenizer.tokenize(text)


if __name__ == "__main__":
    # Test text with various challenging cases
    test_text: str = """
    Dr. Smith (Ph.D., M.D.) visited Washington D.C. on Jan. 20, 2024! He met with Prof. Johnson at 3:30 p.m.
    They discussed A.I. and machine learning... "What about the U.S. market?" asked Dr. Smith.
    The meeting ended at 5 p.m. Later, they went to Mr. Wilson's house (located at 123 Main St.) for dinner.

    Visit our website at https://www.example.com or email us at test@example.com!
    The temperature was 72.5°F (22.5°C). The company's Q3 2023 revenue was $12.5M USD.

    「これは日本語の文章です。」This is a mixed-language text! How cool is that?

    Some technical specs: CPU: 3.5GHz, RAM: 16GB, Storage: 2TB SSD.
    Common abbreviations: etc., i.e., e.g., vs., cf., approx. 100 units.
    """

    # Process and print each sentence
    sentences: List[str] = split_sentences(test_text)
    print("Detected sentences:")
    print("-" * 80)
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")
        print("-" * 80)
