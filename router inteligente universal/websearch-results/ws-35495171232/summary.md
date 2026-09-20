# Web search: Hugging Face Jobs volumes mount hf://models read-only expose port pricing per hour flavors timeout vLLM

- Run: `ws-35495171232`
- Resultados: **8**
- LLM usado: **no**

## Fuentes

### 1. Run a vLLM Server on HF Jobs in One Command
- URL: https://huggingface.co/blog/vllm-jobs
- Proveedores: ddgs
- Score: 1.0
- Extracto: June 26, 2026 - One thing to set up first: agents drive the model through tool calls, and vLLM only accepts those if the server is launched with tool calling enabled. So relaunch with --enable-auto-tool-choice and a --tool-call-parser matching the model family (hermes for Qwen3). Agents also benefit from a stronger model, so this is a good place to bring in the bigger one: hf jobs run --flavor h200x2 --expose 8000 --timeout 2h \ vllm/vllm-openai:latest \ vllm serve Qwen/Qwen3.5-122B-A10B \ --host 0.0.0.0 --port 8000 --tensor-parallel-size 2 \ --max-model-len 32768 --max-num-seqs 256 \ --reasoning-parser deepseek_r1 \ --enable-auto-tool-choice --tool-call-parser hermes

### 2. Serve Models on Jobs · Hugging Face
- URL: https://huggingface.co/docs/hub/jobs-serving
- Proveedores: ddgs
- Score: 0.93
- Extracto: The same applies to any other ... — and its billing — stops when you cancel it or when its timeout is reached (30 minutes by default; set --timeout explicitly for longer sessions):...

### 3. Model volume mounting | Vllm Advanced Course | The Neural Base
- URL: https://theneuralbase.com/vllm/learn/advanced/model-volume-mounting
- Proveedores: ddgs
- Score: 0.86
- Extracto: Predownload step: run huggingfacecli download in the container once with write access, then snapshot that volume and mount readonly for all subsequent deployments. # FIX: Always set BOTH HF_HOME and HF_HUB_CACHE to the same path # HF_HOME alone is insufficient in vLLM v0.6.0+ — some cache operations use HF_HUB_CACHE directly docker run v /path/to/models:/models:ro \ e HF_HOME=/models \ e HF_HUB_CACHE=/models \ vllm/vllmopenai:latest \ vllm serve metallama/Llama3.28BInstruct # FIX: Kubernetes — ensure PersistentVolume and PersistentVolumeClaim binding before Pod admission # Apply in order:

### 4. GitHub - huggingface/hf-mount: Mount Hugging Face Buckets and repos as local filesystems. No download, no copy, no waiting. · GitHub
- URL: https://github.com/huggingface/hf-mount
- Proveedores: ddgs
- Score: 0.79
- Extracto: July 9, 2026 - Useful when several machines or processes need to share a read-only remote view but each layer their own files on top — for example, a shared compilation cache where producer machines populate a bucket with compiled artifacts (torch.compile, vLLM, JAX/XLA, AWS Neuron) and every consumer mounts the same bucket with --overlay.

### 5. Model volume mount hardcodes readOnly: true, breaking HuggingFace cache writes · Issue #243 · llm-d-incubation/llm-d-modelservice
- URL: https://github.com/llm-d-incubation/llm-d-modelservice/issues/243
- Proveedores: ddgs
- Score: 0.72
- Extracto: March 18, 2026 - The chart hardcodes readOnly: true on the model PVC mount, which breaks vLLM startup when using PVC-based model storage with HuggingFace cache structure. ... When using pvc+hf:// URI scheme, the chart mounts the PVC with readOnly: true.

### 6. Pricing and Billing · Hugging Face
- URL: https://huggingface.co/docs/hub/en/jobs-pricing
- Proveedores: ddgs
- Score: 0.65
- Extracto: Hugging Face Jobs let you run compute tasks on Hugging Face infrastructure without managing it yourself. Simply define a command, a Docker image, and a hardware flavor among various CPU and GPU options.

### 7. Configuration · Hugging Face
- URL: https://huggingface.co/docs/hub/en/jobs-configuration
- Proveedores: ddgs
- Score: 0.58
- Extracto: >>> hf jobs uv run --with trl --flavor a10g-small -s HF_TOKEN -- sft.py --model_name_or_path Qwen/Qwen2-0.5B ...

### 8. Hugging Face model management with persistent volume | Moreh
- URL: https://docs.moreh.io/best_practices/hf_model_management_with_pv
- Proveedores: ddgs
- Score: 0.51
- Extracto: apiVersion: odin.moreh.io/v1alpha1 kind: InferenceService metadata: name: llama3-1b-instruct-no-template namespace: spec: template: spec: containers: - name: main image: 255250787067.dkr.ecr.ap-northeast-2.amazonaws.com/quickstart/moreh-vllm:20250915.1 command: - vllm - serve args: - meta-llama/Llama-3.2-1B-Instruct - --port - "8000" env: - name: HF_HOME value: /mnt/models - name: HF_HUB_OFFLINE value: "1" resources: requests: amd.com/gpu: "1" limits: amd.com/gpu: "1" ports: - name: http containerPort: 8000 readinessProbe: httpGet: path: /health port: 8000 scheme: HTTP initialDelaySeconds: 10 periodSeconds: 10 timeoutSeconds: 5 successThreshold: 1 failureThreshold: 3 volumeMounts: - name: models mountPath: /mnt/models volumes: - name: models persistentVolumeClaim: claimName: models tolerations: - key: amd.com/gpu operator: Exists effect: NoSchedule

## Estado de proveedores

```json
{
  "ddgs": {
    "results": 8,
    "state": "PASS"
  }
}
```
