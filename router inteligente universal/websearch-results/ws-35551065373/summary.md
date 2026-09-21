# Web search: Nanbeige4.2-3B GGUF Q4_K_M llama.cpp

- Run: `ws-35551065373`
- Resultados: **8**
- LLM usado: **no**

## Fuentes

### 1. Nanbeige/Nanbeige4.2-3B · Hugging Face
- URL: https://huggingface.co/Nanbeige/Nanbeige4.2-3B
- Proveedores: ddgs
- Score: 1.0
- Extracto: July 27, 2026 - # Option 1: pull a published model (no Modelfile on the client) ./ollama serve ./ollama run nanbeige/nanbeige4.2:3b-Q4_K_M · # Option 2: create from a local .gguf produced by llama.cpp # (see convert_hf_to_gguf.py / llama-quantize above) MODEL_PATH_GGUF_Q4_K_M=/path/to/your/Nanbeige4.2-3B-Q4_K_M.gguf # Modelfile cat > Modelfile <<EOF FROM ${MODEL_PATH_GGUF_Q4_K_M} PARAMETER temperature 0.6 PARAMETER top_p 0.95 PARAMETER top_k 20 EOF ./ollama serve ./ollama create nanbeige42-local -f Modelfile ./ollama run nanbeige42-local

### 2. Abiray/Nanbeige4.2-3B-GGUF · Hugging Face
- URL: https://huggingface.co/Abiray/Nanbeige4.2-3B-GGUF
- Proveedores: ddgs
- Score: 0.93
- Extracto: # Clone the repository with Nanbeige support git clone -b nanbeige42 [https://github.com/Nanbeige/llama.cpp.git](https://github.com/Nanbeige/llama.cpp.git) cd llama.cpp # Build with CUDA support cmake -B build -DGGML_CUDA=ON cmake --build build --config Release -j # Download a model from this repository huggingface-cli download Abiray/Nanbeige4.2-3B-GGUF Nanbeige4.2-3B-Q4_K_M.gguf --local-dir .

### 3. Edge-Quant/Nanbeige4.1-3B-Q4_K_M-GGUF · Hugging Face
- URL: https://huggingface.co/Edge-Quant/Nanbeige4.1-3B-Q4_K_M-GGUF
- Proveedores: ddgs
- Score: 0.86
- Extracto: Invoke the llama.cpp server or the CLI. llama-cli --hf-repo Edge-Quant/Nanbeige4.1-3B-Q4_K_M-GGUF --hf-file nanbeige4.1-3b-q4_k_m.gguf -p "The meaning to life and the universe is"

### 4. enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF · Hugging Face
- URL: https://huggingface.co/enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF
- Proveedores: ddgs
- Score: 0.79
- Extracto: Invoke the llama.cpp server or the CLI. llama-cli --hf-repo enacimie/Nanbeige4-3B-Base-Q4_K_M-GGUF --hf-file nanbeige4-3b-base-q4_k_m.gguf -p "The meaning to life and the universe is"

### 5. bartowski/Nanbeige_Nanbeige4.2-3B-GGUF · Hugging Face
- URL: https://huggingface.co/bartowski/Nanbeige_Nanbeige4.2-3B-GGUF
- Proveedores: ddgs
- Score: 0.72
- Extracto: Some of these quants (Q3_K_XL, Q4_K_L etc) are the standard quantization method with the embeddings and output weights quantized to Q8_0 instead of what they would normally default to. ... huggingface-cli download bartowski/Nanbeige_Nanbeige4.2-3B-GGUF --include "Nanbeige_Nanbeige4.2-3B-Q4_K_M.gguf" --local-dir ./

### 6. owao/Nanbeige4.2-3B-GGUF · Hugging Face
- URL: https://huggingface.co/owao/Nanbeige4.2-3B-GGUF
- Proveedores: ddgs
- Score: 0.65
- Extracto: GGUF quantized versions of Nanbeige4.2-3B.

### 7. arunb74/Nanbeige4.2-3B · Hugging Face
- URL: https://huggingface.co/arunb74/Nanbeige4.2-3B
- Proveedores: ddgs
- Score: 0.58
- Extracto: ./build/bin/llama-server \ -m Nanbeige4.2-3B-Q4_K_M.gguf \ --host 0.0.0.0 \ --port 8080 \ -ngl 999 \ -c 65536

### 8. tantk/Nanbeige4.1-3B-GGUF · Hugging Face
- URL: https://huggingface.co/tantk/Nanbeige4.1-3B-GGUF
- Proveedores: ddgs
- Score: 0.51
- Extracto: GGUF quantizations of Nanbeige/Nanbeige4.1-3B for use with llama.cpp, Ollama, and other GGUF-compatible tools. # Download a specific quantization (e.g. Q4_K_M) ollama run hf.co/tantk/Nanbeige4.1-3B-GGUF:Q4_K_M # Or create from a downloaded file ollama create nanbeige4.1-3b -f Modelfile

## Estado de proveedores

```json
{
  "ddgs": {
    "results": 8,
    "state": "PASS"
  }
}
```
