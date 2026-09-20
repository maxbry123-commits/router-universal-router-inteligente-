# Web search: Hugging Face Spaces mount Storage Bucket volume persistent storage Docker Space 2026

- Run: `ws-35494047636`
- Resultados: **8**
- LLM usado: **no**

## Fuentes

### 1. Disk usage on Spaces · Hugging Face
- URL: https://huggingface.co/docs/hub/en/spaces-storage
- Proveedores: ddgs
- Score: 1.0
- Extracto: This disk space is ephemeral, meaning its content will be lost if your Space restarts or is stopped. If you need to persist data with a longer lifetime than the Space itself, you can attach one or more Storage Buckets as volumes.

### 2. Storage Buckets for Spaces
- URL: https://huggingface.co/changelog/storage-buckets-for-spaces
- Proveedores: ddgs
- Score: 0.93
- Extracto: March 31, 2026 - Hugging Face Changelog - Storage Buckets for Spaces

### 3. GitHub - huggingface/hf-mount: Mount Hugging Face Buckets and repos as local filesystems. No download, no copy, no waiting. · GitHub
- URL: https://github.com/huggingface/hf-mount
- Proveedores: ddgs
- Score: 0.86
- Extracto: July 9, 2026 - Mount Hugging Face Buckets and repos as local filesystems. No download, no copy, no waiting. - huggingface/hf-mount

### 4. Using persistent storage on HF spaces - 🤗Transformers - Hugging Face Forums
- URL: https://discuss.huggingface.co/t/using-persistent-storage-on-hf-spaces/114926
- Proveedores: ddgs
- Score: 0.79
- Extracto: October 31, 2024 - Dears, I am Using persistent storage on HF spaces. 1- Persistent storage acts like traditional disk storage mounted on /data . How to access it or see it in the directory structure… is there a code to mount it or it is mounted by default… If you are using Hugging Face open source libraries, you can make your Space restart faster by setting the environment variable HF_HOME to /data/.huggingface .

### 5. Introducing hf-mount
- URL: https://huggingface.co/changelog/hf-mount
- Proveedores: ddgs
- Score: 0.72
- Extracto: March 24, 2026 - It allows you to attach remote storage that is 100x bigger than your local machine's disk. This is also perfect for Agentic storage! Read-write for Storage Buckets, read-only for models and datasets.

### 6. Spaces Persistent Storage Upgrade Not Accessible - Spaces - Hugging Face Forums
- URL: https://discuss.huggingface.co/t/spaces-persistent-storage-upgrade-not-accessible/171226
- Proveedores: ddgs
- Score: 0.65
- Extracto: December 6, 2025 - Hi, I am working on a small space for my Master’s project which will log and store session data during usage. I was storing this in /tmp and recently moved to /data. On the free tier this is still ephemeral, which I expected, however I have no option to upgrade to a paid tier to activate the persistent storage.

### 7. Docker Spaces · Hugging Face
- URL: https://huggingface.co/docs/hub/spaces-sdks-docker
- Proveedores: ddgs
- Score: 0.58
- Extracto: The data written on disk is lost whenever your Docker Space restarts. To persist data across restarts, you can attach a Storage Bucket to your Space.

### 8. How to mount persistent disk to HF Spaces In Docker? - Spaces - Hugging Face Forums
- URL: https://discuss.huggingface.co/t/how-to-mount-persistent-disk-to-hf-spaces-in-docker/54161
- Proveedores: ddgs
- Score: 0.51
- Extracto: September 8, 2023 - The new persistent storage seems fantastic. How do I mount the storage into the Docker container on spaces? An update to the documentation would be welcome here!

## Estado de proveedores

```json
{
  "ddgs": {
    "results": 8,
    "state": "PASS"
  }
}
```
