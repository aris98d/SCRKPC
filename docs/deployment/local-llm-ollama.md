# 本地 Ollama 模型部署说明

## 1. 安装 Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

## 2. 启动 Ollama

ollama serve

## 3. 模型下载

ollama pull qwen2.5:7b-instruct

## 4. 配置环境变量

LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b-instruct

## 5. 测试模型

cd backend
source .venv/bin/activate
python scripts/test_local_llm.py