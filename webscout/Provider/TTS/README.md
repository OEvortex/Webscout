# 🎙️ Webscout Text-to-Speech (TTS) Providers

## Overview

Webscout's TTS Providers offer a versatile and powerful text-to-speech conversion library with support for multiple providers and advanced features.

## 🌟 Features

- **Multiple TTS Providers**: Support for various text-to-speech services
- **Concurrent Audio Generation**: Efficiently process long texts
- **Flexible Voice Selection**: Choose from a wide range of voices
- **Robust Error Handling**: Comprehensive logging and error management
- **Temporary File Management**: Automatically manages temporary audio files
- **Cross-Platform Compatibility**: Works seamlessly across different environments
- **Custom Save Locations**: Save audio files to specific destinations
- **Audio Streaming**: Stream audio data in chunks for real-time applications

## 📦 Supported TTS Providers

1. **ElevenlabsTTS**
2. **MurfAITTS**
3. **ParlerTTS**
4. **DeepgramTTS**
5. **StreamElementsTTS**
6. **OpenAIFMTTS**
7. **QwenTTS**
8. **SherpaTTS**
9. **PocketTTS**
10. **FasterQwen3TTS**
## 🚀 Installation

```bash
pip install webscout
```

## 💻 Basic Usage

```python
from webscout.Provider.TTS import ElevenlabsTTS

# Initialize the TTS provider
tts = ElevenlabsTTS()

# Generate speech from text
text = "Hello, this is a test of text-to-speech conversion."
audio_file = tts.tts(text, voice="Brian")

# Save the audio to a specific location
saved_path = tts.save_audio(audio_file, destination="my_speech.mp3")
print(f"Audio saved to: {saved_path}")

# Stream audio in chunks
for chunk in tts.stream_audio(text, voice="Brian"):
    # Process each chunk (e.g., send to a websocket, write to a stream, etc.)
    process_audio_chunk(chunk)
```

## 🎛️ Advanced Configuration

### Voice Selection

Each TTS provider offers multiple voices:

```python
# List available voices
print(tts.all_voices.keys())

# Select a specific voice
audio_file = tts.tts(text, voice="Alice")
```

### Verbose Logging

Enable detailed logging for debugging:

```python
audio_file = tts.tts(text, verbose=True)
```

## 🔧 Provider-Specific Details

### ElevenlabsTTS

- Supports multiple English voices
- Multilingual text-to-speech

### MurfAITTS

- Provides specific voice models
- Supports custom voice descriptions

### ParlerTTS

- Uses Gradio Client for TTS generation
- Supports large and small model variants

### DeepgramTTS

- Multiple voice options
- Advanced voice selection

### StreamElementsTTS

- Wide range of international voices

## 🛡️ Error Handling

```python
try:
    audio_file = tts.tts(text)
except exceptions.FailedToGenerateResponseError as e:
    print(f"TTS generation failed: {e}")
```

## 🌐 Proxy Support

```python
# Use with proxy
tts = ElevenlabsTTS(proxies={
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
})
```

## 💾 Custom Audio Saving

Save generated audio to a specific location:

```python
# Generate speech
audio_file = tts.tts(text, voice="Brian")

# Save to a specific file
tts.save_audio(audio_file, destination="path/to/output.mp3")

# Save to a specific directory with default filename
tts.save_audio(audio_file, destination="path/to/directory/")

# Save with default location (current directory with timestamp)
saved_path = tts.save_audio(audio_file)
print(f"Saved to: {saved_path}")
```

## 📼 Audio Streaming

Stream audio data in chunks for real-time applications:

```python
# Stream audio in chunks
for chunk in tts.stream_audio(text, voice="Brian", chunk_size=2048):
    # Example: Send to a websocket
    websocket.send(chunk)

    # Example: Write to an audio stream
    audio_stream.write(chunk)

    # Example: Process in real-time
    process_audio_data(chunk)
```

## ⏱️ Async Support

Use the async versions for non-blocking operations:

```python
from webscout.Provider.TTS import AsyncElevenlabsTTS
import asyncio

async def main():
    tts = AsyncElevenlabsTTS()

    # Generate speech
    audio_file = await tts.tts(text, voice="Brian")

    # Save to a specific location
    saved_path = await tts.save_audio(audio_file, destination="output.mp3")

    # Stream audio
    async for chunk in tts.stream_audio(text, voice="Brian"):
        await process_chunk(chunk)

asyncio.run(main())
```
