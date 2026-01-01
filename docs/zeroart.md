# ZeroArt: Zero-Dependency ASCII Art Generator

Generate stunning ASCII art text with zero external dependencies.

## Overview

ZeroArt is a powerful, lightweight Python library for generating ASCII art text without any external dependencies. Transform plain text into eye-catching, stylized art with just a few lines of code.

## Features

- **Multiple Font Styles**
  - Block Font - Classic bold block letters
  - Slant Font - Elegant slanted text
  - Neon Font - Glowing pixel-style art
  - Cyber Font - Cyberpunk-inspired rendering
  - 3D Font - Text with 3D depth effect
  - Electronic Font - Digital-style text
  - Isometric Font - Text with isometric perspective

- **Zero Dependencies**
  - Completely standalone library
  - No external package requirements

- **Easy to Use**
  - Simple, intuitive API
  - Minimal setup needed

- **Text Effects**
  - Rainbow coloring - ANSI color cycling
  - Glitch effect - Random character distortion
  - Text wrapping - Auto-wrap to specified width
  - Outline generation - Border characters around art
  - Gradient effect - Smooth color transitions
  - Bouncing effect - Animated bounce simulation

## Installation

No installation required. ZeroArt is included with Webscout:

```python
from webscout import zeroart
```

## Usage

### Basic ASCII Art

```python
from webscout import zeroart

# Generate ASCII art
art = zeroart.figlet_format("PYTHON", font='block')
print(art)

# Directly print ASCII art
zeroart.print_figlet("CODING", font='slant')
```

### Font Styles

```python
from webscout import zeroart

# Different font styles
print(zeroart.figlet_format("AWESOME", font='block'))      # Block style
print(zeroart.figlet_format("CODING", font='slant'))      # Slant style
print(zeroart.figlet_format("NEON", font='neon'))         # Neon style
print(zeroart.figlet_format("CYBER", font='cyber'))       # Cyber style
print(zeroart.figlet_format("3D", font='3d'))             # 3D style
print(zeroart.figlet_format("ELECTRONIC", font='electronic')) # Electronic style
print(zeroart.figlet_format("ISOMETRIC", font='isometric')) # Isometric style
```

### Text Effects

```python
from webscout import zeroart

# Rainbow effect - cycles through ANSI colors
print(zeroart.rainbow("COLORFUL", font='neon'))

# Glitch effect - random character distortion
print(zeroart.glitch("GLITCH", font='cyber', glitch_intensity=0.15))

# Outline effect - adds border characters
print(zeroart.outline("BORDER", font='block', outline_char='#'))

# Gradient effect - smooth color transition
print(zeroart.gradient("GRADIENT", font='3d', color1=(255,0,0), color2=(0,0,255)))

# Bouncing effect - animated bounce simulation
print(zeroart.bounce("BOUNCE", font='electronic', bounce_height=3))

# Text wrapping
wrapped = zeroart.wrap_text("Very long text that needs wrapping", width=20)
print(wrapped)
```

### Custom Font Class

```python
from webscout.zeroart import ZeroArtFont

class CustomFont(ZeroArtFont):
    def __init__(self):
        super().__init__("custom")
        self.letters = {
            'A': ["  /\\  ", " /--\\ ", "/----\\", "/      \\"],
            # ... add more letters
        }

# Use custom font
font = CustomFont()
print(font.render("TEST"))
```

## API Reference

### `figlet_format(text: str, font: Union[str, ZeroArtFont] = 'block') -> str`

Generate ASCII art representation of text.

**Parameters:**
- `text` (str): Text to convert
- `font` (str | ZeroArtFont): Font style name or ZeroArtFont instance. Default: 'block'

**Returns:**
- `str`: ASCII art representation of text

**Font names:** `'block'`, `'slant'`, `'neon'`, `'cyber'`, `'dotted'`, `'shadow'`, `'3d'`, `'electronic'`, `'isometric'`

### `print_figlet(text: str, font: Union[str, ZeroArtFont] = 'block') -> None`

Print ASCII art directly to stdout.

**Parameters:**
- `text` (str): Text to convert and print
- `font` (str | ZeroArtFont): Font style name or ZeroArtFont instance. Default: 'block'

### `rainbow(text: str, font: Union[str, ZeroArtFont] = 'block') -> str`

Apply rainbow ANSI color cycling to ASCII art.

**Parameters:**
- `text` (str): Text to render
- `font` (str | ZeroArtFont): Font style to use. Default: 'block'

**Returns:**
- `str`: Rainbow-colored ASCII art

### `glitch(text: str, font: Union[str, ZeroArtFont] = 'block', glitch_intensity: float = 0.1) -> str`

Apply glitch distortion to ASCII art.

**Parameters:**
- `text` (str): Text to render
- `font` (str | ZeroArtFont): Font style to use. Default: 'block'
- `glitch_intensity` (float): Probability of character distortion (0.0-1.0). Default: 0.1

**Returns:**
- `str`: Glitched ASCII art

### `outline(text: str, font: Union[str, ZeroArtFont] = 'block', outline_char: str = '*') -> str`

Add outline characters around ASCII art.

**Parameters:**
- `text` (str): Text to render
- `font` (str | ZeroArtFont): Font style to use. Default: 'block'
- `outline_char` (str): Character to use for outline. Default: '*'

**Returns:**
- `str`: ASCII art with outline

### `gradient(text: str, font: Union[str, ZeroArtFont] = 'block', color1: tuple = (255,0,0), color2: tuple = (0,0,255)) -> str`

Apply gradient color effect to ASCII art.

**Parameters:**
- `text` (str): Text to render
- `font` (str | ZeroArtFont): Font style to use. Default: 'block'
- `color1` (tuple): Starting RGB color as (r,g,b). Default: (255,0,0)
- `color2` (tuple): Ending RGB color as (r,g,b). Default: (0,0,255)

**Returns:**
- `str`: Gradient-styled ASCII art

### `bounce(text: str, font: Union[str, ZeroArtFont] = 'block', bounce_height: int = 2) -> str`

Create bouncing text effect.

**Parameters:**
- `text` (str): Text to render
- `font` (str | ZeroArtFont): Font style to use. Default: 'block'
- `bounce_height` (int): Height of bounce effect. Default: 2

**Returns:**
- `str`: Bouncing ASCII art

### `wrap_text(text: str, width: int = 20) -> str`

Wrap text to specified width.

**Parameters:**
- `text` (str): Text to wrap
- `width` (int): Maximum line width. Default: 20

**Returns:**
- `str`: Wrapped text

## Font Classes

### ZeroArtFont

Base class for all ASCII art fonts.

**Methods:**
- `__init__(name: str)`: Initialize font with name
- `add_letter(char: str, art_lines: List[str])`: Add custom letter to font
- `add_special_char(name: str, art_lines: List[str])`: Add special character
- `get_letter(char: str) -> List[str]`: Get ASCII art for a character
- `render(text: str) -> str`: Render text as ASCII art

**Attributes:**
- `name` (str): Font name
- `letters` (Dict[str, List[str]]): Character to ASCII art mapping
- `special_chars` (Dict[str, List[str]]): Special character mapping

### Available Fonts

- **BlockFont**: Classic, bold block-style letters
- **SlantFont**: Elegant, slanted text
- **NeonFont**: Glowing, pixel-style art
- **CyberFont**: Cyberpunk-inspired rendering
- **DottedFont**: Dotted-style letters
- **ShadowFont**: Letters with drop shadow effect
- **ThreeDFont**: Text with 3D depth
- **ElectronicFont**: Digital-style text
- **IsometricFont**: Text with isometric perspective

## Notes

- All fonts support uppercase letters A-Z
- Special characters and lowercase letters fall back to space
- Color effects use ANSI escape codes (works in most terminals)
- Some fonts may have varying heights
