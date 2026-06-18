<div align="center">
  <a href="https://github.com/OEvortex/Webscout">
    <img src="https://img.shields.io/badge/WebScout-GGUF%20Converter%20v2.0-blue?style=for-the-badge&logo=python&logoColor=white" alt="GGUF Converter Logo">
  </a>

  <h1>GGUF Converter v2.0</h1>

  <p><strong>Convert Hugging Face models to GGUF format with advanced quantization options</strong></p>

  <p>
    Transform large language models from Hugging Face into optimized GGUF format for efficient inference on consumer hardware. 
    Now with remote mode, multiple output types, and the latest llama.cpp features.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://github.com/ggerganov/llama.cpp"><img src="https://img.shields.io/badge/Powered%20by-llama.cpp-orange?style=flat-square" alt="Powered by llama.cpp"></a>
    <a href="https://huggingface.co/"><img src="https://img.shields.io/badge/Hugging%20Face-compatible-yellow?style=flat-square" alt="Hugging Face compatible"></a>
    <a href="#"><img src="https://img.shields.io/badge/GPU-acceleration-green?style=flat-square" alt="GPU acceleration"></a>
    <a href="#"><img src="https://img.shields.io/badge/Version-2.0.0-purple?style=flat-square" alt="Version 2.0.0"></a>
  </p>
</div>

<hr/>

## 📋 Table of Contents

- [🌟 Features](#-features)
- [🆕 What's New in v2.0](#-whats-new-in-v20)
- [⚙️ Installation](#️-installation)
- [🛠️ Basic Usage](#️-basic-usage)
- [🧩 Advanced Options](#-advanced-options)
- [📊 Quantization Methods](#-quantization-methods)
- [📏 Size & Quality Comparison](#-size--quality-comparison)
- [📦 Hardware Requirements](#-hardware-requirements)
- [⚡ Examples](#-examples)
- [🔍 Troubleshooting](#-troubleshooting)
- [🧠 Technical Details](#-technical-details)

<hr/>

## 🌟 Features

<details open>
<summary><b>Core Capabilities</b></summary>
<p>

* **Multiple Output Types**: Support for f32, f16, bf16, q8_0, tq1_0, tq2_0, and auto-detection
* **30+ Quantization Methods**: From 1-bit to 32-bit precision with K-quant and IQ variants
* **Importance Matrix Quantization**: Enhanced precision with IQ1, IQ2, IQ3, IQ4 methods
* **Remote Mode (Experimental)**: Convert models without downloading full weights to disk
* **Model Splitting**: Split large models into manageable chunks with K/M/G size units
* **Hardware Acceleration Detection**: Automatically detects CUDA, Metal, OpenCL, Vulkan, ROCm
* **Hugging Face Integration**: Direct download from and upload to Hugging Face repositories
* **README Generation**: Automatically creates documentation for your quantized models
* **Dry Run Mode**: Preview split plans before writing any files
</p>
</details>

<hr/>

## 🆕 What's New in v2.0

<details open>
<summary><b>New Features (December 2024)</b></summary>
<p>

| Feature | Description |
|---------|-------------|
| **Output Types** | New `--outtype` option: f32, f16, bf16, q8_0, tq1_0, tq2_0, auto |
| **Remote Mode** | `--remote` flag to read tensors without full download |
| **Dry Run** | `--dry-run` to preview split plans without writing files |
| **Vocab Only** | `--vocab-only` to extract just vocabulary (no weights) |
| **No Lazy** | `--no-lazy` to disable lazy evaluation (use more RAM) |
| **Model Name** | `--model-name` to override the model name in output |
| **Small First Shard** | `--small-first-shard` for metadata-only first split |
| **New IQ Types** | IQ1, IQ2, IQ3, IQ4 importance-based quantization |
| **K-Quant Updates** | Added q2_k_s, q4_k_l, q5_k_l variants |
| **Ternary Quants** | tq1_0, tq2_0 experimental ternary quantization |

</p>
</details>

<hr/>

## ⚙️ Installation

<div class="installation-box">
<p>The GGUF Converter is included with the WebScout package:</p>

```bash
pip install -U llm4free
```
</div>

<hr/>

## 🛠️ Basic Usage

The simplest way to convert a model is with the default settings:

```bash
python -m llm4free.Extra.gguf convert -m "organization/model-name"
```

This will:
1. Download the model from Hugging Face
2. Convert it to GGUF format with f16 base and q4_k_m quantization
3. Save the converted model in your current directory

<hr/>

## 🧩 Advanced Options

<details open>
<summary><b>Command Reference</b></summary>
<p>

The full command syntax is:

```
python -m llm4free.Extra.gguf convert [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-m, --model-id` | The HuggingFace model ID (e.g., 'OEvortex/HelpingAI-Lite-1.5T') | **Required** |
| `-u, --username` | Your HuggingFace username for uploads | None |
| `-t, --token` | Your HuggingFace API token for uploads | None |
| `-q, --quantization` | Comma-separated quantization methods | "q4_k_m" |
| `-o, --outtype` | Output type: f32, f16, bf16, q8_0, tq1_0, tq2_0, auto | "f16" |
| `-i, --use-imatrix` | Use importance matrix for quantization | False |
| `--train-data` | Training data file for imatrix quantization | None |
| `-s, --split-model` | Split the model into smaller chunks | False |
| `--split-max-tensors` | Maximum number of tensors per file when splitting | 256 |
| `--split-max-size` | Maximum file size when splitting (e.g., '256M', '5G') | None |
| `--vocab-only` | Only extract vocabulary (no model weights) | False |
| `--remote` | (Experimental) Read tensors remotely without full download | False |
| `--dry-run` | Only print split plan without writing files | False |
| `--no-lazy` | Disable lazy evaluation (use more RAM) | False |
| `--model-name` | Custom model name override | None |
| `--small-first-shard` | Do not add tensors to the first split | False |
</p>
</details>

<details>
<summary><b>Output Types</b></summary>
<p>

Choose the base output precision before quantization:

```bash
# Use bfloat16 (good for models trained with bf16)
python -m llm4free.Extra.gguf convert -m "organization/model-name" -o "bf16"

# Use auto-detection based on model's tensor types
python -m llm4free.Extra.gguf convert -m "organization/model-name" -o "auto"

# Use 8-bit quantization directly
python -m llm4free.Extra.gguf convert -m "organization/model-name" -o "q8_0"
```
</p>
</details>

<details>
<summary><b>Multiple Quantization Methods</b></summary>
<p>

Apply multiple quantization methods at once:

```bash
python -m llm4free.Extra.gguf convert -m "organization/model-name" -q "q4_k_m,q5_k_m"
```

This will create two versions of the model with different quantization methods.
</p>
</details>

<details>
<summary><b>Remote Mode (Experimental)</b></summary>
<p>

Convert models without downloading the full weights to disk:

```bash
python -m llm4free.Extra.gguf convert -m "organization/model-name" --remote
```

This downloads only config and tokenizer files, streaming tensor data directly from HuggingFace.
Useful for systems with limited disk space.
</p>
</details>

<details>
<summary><b>Uploading to Hugging Face</b></summary>
<p>

Convert and upload the model to your Hugging Face account:

```bash
python -m llm4free.Extra.gguf convert -m "organization/model-name" -u "your-username" -t "your-token"
```

This will create a new repository in your account named `model-name-GGUF` containing the converted model.
</p>
</details>

<details>
<summary><b>Importance Matrix Quantization</b></summary>
<p>

Use importance matrix for more efficient quantization:

```bash
python -m llm4free.Extra.gguf convert -m "organization/model-name" -i --train-data "train_data.txt" -q "iq4_nl"
```

Importance matrix helps focus more bits on weights that matter most for the model's performance.
</p>
</details>

<details>
<summary><b>Model Splitting</b></summary>
<p>

Split large models for easier distribution:

```bash
# Split by number of tensors
python -m llm4free.Extra.gguf convert -m "organization/model-name" -s --split-max-tensors 256

# Split by file size (supports K, M, G units)
python -m llm4free.Extra.gguf convert -m "organization/model-name" -s --split-max-size "2G"

# Preview split plan without writing files
python -m llm4free.Extra.gguf convert -m "organization/model-name" -s --split-max-size "2G" --dry-run
```

This is useful for very large models that may be difficult to distribute as a single file.
</p>
</details>

<hr/>

## 📊 Quantization Methods

<details open>
<summary><b>Standard K-Quant Methods</b></summary>
<p>

| Method | Description |
|--------|-------------|
| `f32` | 32-bit floating point - full precision, largest size |
| `f16` / `fp16` | 16-bit floating point - maximum accuracy, large size |
| `bf16` | bfloat16 - good balance for training and some models |
| `auto` | Auto-detect best 16-bit type based on model tensors |
| `q8_0` | 8-bit quantization - near-original quality |
| `q6_k` | 6-bit K-quant - near-lossless quality |
| `q5_k_l` | 5-bit K-quant large - highest quality 5-bit |
| `q5_k_m` | 5-bit K-quant medium - best balance for quality/size |
| `q5_k_s` | 5-bit K-quant small - optimized for speed |
| `q4_k_l` | 4-bit K-quant large - highest quality 4-bit |
| `q4_k_m` | 4-bit K-quant medium - balanced for most models |
| `q4_k_s` | 4-bit K-quant small - optimized for speed |
| `q3_k_l` | 3-bit K-quant large - balanced for size/accuracy |
| `q3_k_m` | 3-bit K-quant medium - good balance for most use cases |
| `q3_k_s` | 3-bit K-quant small - optimized for speed |
| `q2_k` | 2-bit K-quant - smallest size, lowest accuracy |
| `q2_k_s` | 2-bit K-quant small - maximum compression |
</p>
</details>

<details>
<summary><b>Legacy Quantization Methods</b></summary>
<p>

| Method | Description |
|--------|-------------|
| `q4_0` | 4-bit quantization (legacy) - auto-repacks for ARM |
| `q4_1` | 4-bit quantization (legacy) - improved accuracy |
| `q5_0` | 5-bit quantization (legacy) - high accuracy |
| `q5_1` | 5-bit quantization (legacy) - improved accuracy |
</p>
</details>

<details>
<summary><b>Ternary Quantization (Experimental)</b></summary>
<p>

| Method | Description |
|--------|-------------|
| `tq1_0` | 1-bit ternary quantization - extreme compression |
| `tq2_0` | 2-bit ternary quantization - very small size |
</p>
</details>

<details>
<summary><b>Importance Matrix (IQ) Methods</b></summary>
<p>

These methods require `--use-imatrix` and optionally `--train-data`:

| Method | Description |
|--------|-------------|
| `iq1_s` | 1-bit IQ small - extreme compression |
| `iq1_m` | 1-bit IQ medium - extreme compression |
| `iq2_xxs` | 2-bit IQ extra extra small - maximum compression |
| `iq2_xs` | 2-bit IQ extra small - very high compression |
| `iq2_s` | 2-bit IQ small - high compression |
| `iq2_m` | 2-bit IQ medium - balanced compression |
| `iq3_xxs` | 3-bit IQ extra extra small - maximum compression |
| `iq3_xs` | 3-bit IQ extra small - high compression |
| `iq3_s` | 3-bit IQ small - balanced compression |
| `iq3_m` | 3-bit IQ medium - balanced importance-based |
| `iq4_nl` | 4-bit IQ non-linear - best accuracy for 4-bit |
| `iq4_xs` | 4-bit IQ extra small - maximum 4-bit compression |
</p>
</details>

<hr/>

## 📏 Size & Quality Comparison

> **TIP:**
> When choosing a quantization method, consider the tradeoff between model size and quality. Here's a quick guide:

<div class="comparison-table">

### 1. Maximum Quality (largest size)
- **f32**: 100% of original size, best quality
- **f16/bf16**: 50% of original size, excellent quality
- **q8_0**: 50% of original size, nearly identical to f16

### 2. Balanced Quality/Size
- **q6_k**: 38% of original size, near-lossless
- **q5_k_m with imatrix**: 31% of original size, excellent quality
- **q4_k_m with imatrix**: 25% of original size, good quality for most use cases

### 3. Minimum Size (reduced quality)
- **q3_k_s**: 18% of original size, acceptable for some tasks
- **q2_k**: 12% of original size, significantly reduced quality
- **iq2_xxs with imatrix**: 10% of original size, requires careful calibration
</div>

<hr/>

## 📦 Hardware Requirements

Hardware requirements vary based on quantization method and model size:

<details open>
<summary><b>Memory Requirements</b></summary>
<p>

| Quantization | RAM Required |
|--------------|--------------|
| f32 | ~4x model size |
| f16/bf16 | ~2x model size |
| q8_0 | ~1x model size |
| q4_k_m | ~0.5x model size |
| q2_k | ~0.25x model size |

For example, a 7B parameter model requires:
- f16: ~14GB RAM
- q4_k_m: ~3.5GB RAM
</p>
</details>

<details>
<summary><b>Hardware Acceleration</b></summary>
<p>

The converter automatically detects and utilizes:
- **CUDA** for NVIDIA GPUs
- **Metal** for Apple Silicon and AMD GPUs on macOS
- **OpenCL** for cross-platform GPU acceleration
- **Vulkan** for cross-platform GPU acceleration
- **ROCm** for AMD GPUs on Linux

If no acceleration is available, the converter will use CPU-only mode.
</p>
</details>

> **NOTE:**
> **GPU acceleration is highly recommended** for converting larger models (13B+).

<hr/>

## ⚡ Examples

<details open>
<summary><b>Basic Conversion with Upload</b></summary>
<p>

```bash
python -m llm4free.Extra.gguf convert \
    -m "mistralai/Mistral-7B-Instruct-v0.2" \
    -q "q4_k_m" \
    -o "f16" \
    -u "your-username" \
    -t "your-token"
```

This will convert Mistral-7B to q4_k_m quantization and upload it to your Hugging Face account.
</p>
</details>

<details>
<summary><b>bfloat16 Base with Multiple Quantizations</b></summary>
<p>

```bash
python -m llm4free.Extra.gguf convert \
    -m "meta-llama/Meta-Llama-3-8B" \
    -o "bf16" \
    -q "q4_k_m,q5_k_m,q6_k"
```

This will create three versions of the model starting from bf16 base.
</p>
</details>

<details>
<summary><b>IQ Quantization with Importance Matrix</b></summary>
<p>

```bash
python -m llm4free.Extra.gguf convert \
    -m "mistralai/Mistral-7B-Instruct-v0.2" \
    -q "iq4_nl,iq3_m" \
    -i \
    --train-data "my_training_data.txt"
```

This will create two IQ-quantized versions using importance matrix for better quality.
</p>
</details>

<details>
<summary><b>Remote Mode (Experimental)</b></summary>
<p>

```bash
python -m llm4free.Extra.gguf convert \
    -m "meta-llama/Meta-Llama-3-8B" \
    --remote \
    -q "q4_k_m"
```

Convert without downloading full model weights (streams from HuggingFace).
</p>
</details>

<details>
<summary><b>Split Large Model with Dry Run</b></summary>
<p>

```bash
# Preview the split plan first
python -m llm4free.Extra.gguf convert \
    -m "meta-llama/Llama-2-70b-chat-hf" \
    -q "q4_k_m" \
    -s \
    --split-max-size "4G" \
    --dry-run

# Then actually perform the split
python -m llm4free.Extra.gguf convert \
    -m "meta-llama/Llama-2-70b-chat-hf" \
    -q "q4_k_m" \
    -s \
    --split-max-size "4G"
```

This will split the large 70B model into multiple files, each no larger than 4GB.
</p>
</details>

<hr/>

## 🔍 Troubleshooting

<details>
<summary><b>Missing Dependencies</b></summary>
<p>

```
Error: Missing required dependencies: git, cmake
```

**Solution:** Install the required system dependencies:

- **Ubuntu/Debian:** `sudo apt install git cmake python3-dev build-essential`
- **macOS:** `brew install git cmake`
- **Windows:** Install Git and CMake from their respective websites

For hardware acceleration, install relevant drivers (CUDA, ROCm, etc.)
</p>
</details>

<details>
<summary><b>Out of Memory</b></summary>
<p>

```
Error: CUDA out of memory
```

**Solutions:**
1. Try a lower precision quantization method: `q3_k_s` or `q2_k`
2. Enable model splitting with `-s`
3. Use `--no-lazy` to disable lazy evaluation (uses more RAM but may help)
4. Try remote mode with `--remote` to reduce disk I/O
5. Increase your system's swap space/virtual memory
</p>
</details>

<details>
<summary><b>Invalid Output Type</b></summary>
<p>

```
Error: Invalid output type: xxx
```

**Solution:** Use a valid output type:
- `f32` - Full 32-bit precision
- `f16` - Half 16-bit precision
- `bf16` - bfloat16 precision
- `q8_0` - 8-bit quantization
- `tq1_0` - 1-bit ternary
- `tq2_0` - 2-bit ternary
- `auto` - Auto-detect
</p>
</details>

<details>
<summary><b>Download Failures</b></summary>
<p>

```
Error: Failed to download model
```

**Solutions:**
1. Check your internet connection
2. Verify you have access to the model on Hugging Face
3. Try using a Hugging Face token with `-t`
4. Check if the model repository exists and is public
5. Try `--remote` mode for gated models
</p>
</details>

<details>
<summary><b>Build Failures</b></summary>
<p>

```
Error: Failed to build llama.cpp
```

**Solutions:**
1. Check if you have a C++ compiler installed
2. Ensure you have sufficient disk space
3. Try building with CPU-only mode if GPU builds fail
4. Update your GPU drivers if using acceleration
</p>
</details>

<hr/>

## 🧠 Technical Details

The converter works by following these steps:

1. **Setup**: Clone and build llama.cpp with appropriate hardware acceleration
2. **Download**: Fetch the model from Hugging Face (or use remote streaming)
3. **Convert**: Transform the model to base GGUF format (f16/bf16/f32/q8_0/auto)
4. **Quantize**: Apply the requested quantization methods using llama-quantize
5. **Split**: Optionally split the model into smaller chunks
6. **Upload**: If credentials are provided, upload to Hugging Face

<details>
<summary><b>Advanced Configuration</b></summary>
<p>

For special cases, you may want to modify llama.cpp's build parameters. The converter automatically detects and enables available hardware acceleration, but you can also build llama.cpp manually with custom options before running the converter.

The converter uses the latest llama.cpp features including:
- **GGML_CUDA** for NVIDIA GPU acceleration
- **GGML_METAL** for Apple Silicon
- **GGML_VULKAN** for cross-platform GPU support
- **GGML_OPENCL** for OpenCL acceleration
- **GGML_HIPBLAS** for AMD ROCm support
</p>
</details>

<hr/>

<div align="center">
  <p>
    <a href="https://github.com/OEvortex/Webscout">🔗 Part of the WebScout Project</a> |
    <a href="https://github.com/ggerganov/llama.cpp">🚀 Powered by llama.cpp</a>
  </p>
  
  <p>Made with ❤️ by the LLM4Free team</p>
</div>

<!-- Auto-generated developer documentation summary -->
## Developer Notes (auto-generated)

This section was appended by an automated documentation task for `llm4free/Extra/gguf.py` and summarizes the module's structure and usage:

- Provides ModelConverter for HF->GGUF conversion, quantization, optional imatrix and splitting.
- Includes robust llama.cpp build orchestration, cross-platform hardware detection, and Hugging Face upload helpers.
- CLI entrypoint: `gguf convert` exposing options such as `--quantization`, `--outtype`, `--use-imatrix`, `--split-model`, and upload credentials.

For more details, see the rest of this document and inspect `llm4free/Extra/gguf.py` source directly.
