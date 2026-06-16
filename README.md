# Contract Review Platform

这是一个企业采购合同智能审查 Demo。用户上传采购合同后，后端解析合同文本，调用本地 LLM 抽取结构化字段，再通过规则引擎识别风险，并使用企业采购制度知识库检索制度依据。当前代码已经接入 `pgvector` 向量检索和 `BAAI/bge-reranker-v2-m3` 重排序。

本文档是给后续维护者和 Codex 快速理解项目用的项目索引。读这个 README 后，应能知道项目怎么启动、数据怎么初始化、主要代码在哪里、常见错误怎么处理。

## 当前工作目录

项目根目录：

```bash
/home/aris/contract-review-platform
```

后端目录：

```bash
/home/aris/contract-review-platform/backend
```

## 系统流程

```text
前端上传 txt/docx/pdf 合同
  -> FastAPI /api/contracts/review-demo
  -> 保存到 backend/uploads/
  -> document_parser 解析纯文本
  -> field_extractor 调用本地 LLM 抽取合同字段
  -> rules 执行规则审查
  -> vector_retriever 用 bge-m3 + pgvector 检索制度依据
  -> reranker_service 用 bge-reranker-v2-m3 重排序
  -> 返回字段、风险项、制度依据给前端展示
```

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/contracts.py          # 上传合同并触发审查的 API
│   │   ├── core/config.py            # .env 配置读取
│   │   ├── db/session.py             # SQLAlchemy engine/session
│   │   ├── llm/client.py             # OpenAI-compatible LLM 客户端
│   │   ├── models/knowledge.py       # document_chunks 表，pgvector 向量列
│   │   ├── rag/
│   │   │   ├── policy_loader.py      # 切分 sample-data/knowledge/purchase_policy.txt
│   │   │   ├── policy_retriever.py   # 旧的关键词检索
│   │   │   ├── vector_retriever.py   # 当前主要使用的 pgvector 检索
│   │   │   ├── embedding_service.py  # BAAI/bge-m3 embedding
│   │   │   └── reranker_service.py   # BAAI/bge-reranker-v2-m3 重排序
│   │   ├── review/rules.py           # 合同风险规则
│   │   ├── schemas/                  # API 响应和字段模型
│   │   ├── services/
│   │   │   ├── document_parser.py    # txt/docx/pdf 解析
│   │   │   └── field_extractor.py    # LLM 字段抽取 prompt/JSON 解析
│   │   └── main.py                   # FastAPI 入口
│   ├── scripts/
│   │   ├── init_db.py                # 创建 vector 扩展、表、ivfflat 索引
│   │   ├── index_policy_chunks.py    # 制度文本切分、embedding、入库
│   │   ├── test_local_llm.py         # 测试 Ollama/OpenAI-compatible LLM
│   │   └── test_vector_search.py     # 测试 pgvector + reranker 检索
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/App.tsx                   # 单页上传和结果展示
│   └── package.json
├── sample-data/
│   ├── contracts/                    # 测试合同
│   └── knowledge/purchase_policy.txt # 采购合同管理制度知识库源文件
├── docs/deployment/local-llm-ollama.md
├── docker-compose.yml                # pgvector PostgreSQL
└── README.md
```

## 运行依赖

后端：

- Python 3.12
- FastAPI
- SQLAlchemy
- psycopg2
- pgvector
- OpenAI Python SDK
- FlagEmbedding
- PyMuPDF
- python-docx

前端：

- React
- TypeScript
- Vite
- Ant Design
- Axios

外部服务：

- PostgreSQL + pgvector，默认由 `docker-compose.yml` 启动
- Ollama 或其他 OpenAI-compatible Chat Completions 服务
- 默认 LLM：`qwen2.5:7b-instruct`
- 默认 embedding：`BAAI/bge-m3`
- 默认 reranker：`BAAI/bge-reranker-v2-m3`

## 关键配置

后端读取 `backend/.env`，当前常用配置如下：

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:7b-instruct

DATABASE_URL=postgresql+psycopg2://contract_user:contract_pass@localhost:5432/contract_review

EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
EMBEDDING_DEVICE=cuda
EMBEDDING_USE_FP16=true
```

如果机器没有可用 CUDA，把下面两项改成 CPU：

```env
EMBEDDING_DEVICE=cpu
EMBEDDING_USE_FP16=false
```

## 依赖版本注意事项

`use_reranker=True` 依赖版本比较敏感。已经验证可用的组合是：

```text
FlagEmbedding==1.4.0
transformers==4.57.3
huggingface_hub==0.36.2
tokenizers==0.22.2
```

不要随意升级到 `transformers 5.x`。之前的失败现象是：

```text
AttributeError: XLMRobertaTokenizer has no attribute prepare_for_model
```

这是 `FlagReranker.compute_score()` 和 `transformers 5.x` 的兼容性问题。修复方式是保持 `requirements.txt` 中固定的 `transformers==4.57.3`。

## 启动数据库

在项目根目录运行：

```bash
cd /home/aris/contract-review-platform
sudo docker compose up -d postgres
```

数据库服务配置：

```text
host: localhost
port: 5432
user: contract_user
password: contract_pass
database: contract_review
image: pgvector/pgvector:pg16
```

如果拉镜像超时，通常是 Docker Hub 网络问题，不是 compose 配置问题。可先单独测试：

```bash
sudo docker pull pgvector/pgvector:pg16
```

## 初始化向量数据库

进入后端目录：

```bash
cd /home/aris/contract-review-platform/backend
```

创建 `vector` 扩展、`document_chunks` 表和 ivfflat 索引：

```bash
.venv/bin/python -m scripts.init_db
```

把 `sample-data/knowledge/purchase_policy.txt` 切分、embedding 并写入 pgvector：

```bash
.venv/bin/python -m scripts.index_policy_chunks
```

`document_chunks.embedding` 是 `Vector(1024)`，对应 `BAAI/bge-m3` 的 dense embedding 维度。

## 测试向量检索和重排序

```bash
cd /home/aris/contract-review-platform/backend
.venv/bin/python scripts/test_vector_search.py
```

这个脚本当前使用：

```python
rule_code="PAYMENT_PREPAYMENT_LIMIT"
query="合同签订后支付合同总额的50%，是否超过预付款比例限制"
candidate_k=20
top_k=5
use_reranker=True
```

验证通过时会输出 `vector_score` 和 `rerank_score`。当前已验证过 `use_reranker=True` 能正常返回重排序结果，第一条通常是超比例预付款专项审批相关条款：

```text
chunk_id: purchase_policy_0013
rerank_score: 7.90625
```

## 启动后端

```bash
cd /home/aris/contract-review-platform/backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期：

```json
{"status":"ok"}
```

主要 API：

```text
POST /api/contracts/review-demo
Content-Type: multipart/form-data
field: file
supported suffixes: .txt, .docx, .pdf
```

## 启动前端

```bash
cd /home/aris/contract-review-platform/frontend
npm run dev
```

默认访问：

```text
http://localhost:5173
```

前端会把合同上传到：

```text
http://127.0.0.1:8000/api/contracts/review-demo
```

## 本地 LLM

默认使用 Ollama 的 OpenAI-compatible API：

```text
http://127.0.0.1:11434/v1
```

测试脚本：

```bash
cd /home/aris/contract-review-platform/backend
.venv/bin/python scripts/test_local_llm.py
```

后端字段抽取在 `backend/app/services/field_extractor.py`，它要求模型只输出 JSON，并通过 `response_format={"type": "json_object"}` 调用。

## 审查规则

规则入口：

```text
backend/app/review/rules.py
```

当前规则包括：

- `PAYMENT_PREPAYMENT_LIMIT`：预付款比例超过 30%
- `DELIVERY_DATE_MISSING`：交付日期使用“另行协商、待定、双方协商确定”等不确定表述
- `DISPUTE_LOCATION_RISK`：争议解决地为乙方所在地法院
- `AMOUNT_EXTRACTION_INCOMPLETE` / `AMOUNT_CASE_INCONSISTENT`：合同金额大小写信息不完整或不一致

规则命中后会调用：

```python
search_policy_evidence_vector(...)
```

也就是说当前审查结果中的制度依据来自 pgvector 检索和 reranker 重排序。

## RAG 组件

制度源文件：

```text
sample-data/knowledge/purchase_policy.txt
```

切分逻辑：

```text
backend/app/rag/policy_loader.py
```

切分规则按 Markdown 标题层级处理：

- `# 采购合同管理制度` 是文档总标题，不作为 chunk
- `## 第四章 预付款管理` 作为 `chapter_title`
- `### 第十一条 预付款比例控制原则` 作为 `section_title`
- 附件标题也会作为章节或小节

向量检索：

```text
backend/app/rag/vector_retriever.py
```

流程：

```text
rule_code + query
  -> build_rule_query 拼接规则语义说明
  -> embed_query 生成查询向量
  -> DocumentChunk.embedding.cosine_distance(query_embedding)
  -> 取 candidate_k 个候选
  -> rerank(query, candidates)
  -> 返回 top_k
```

旧关键词检索仍保留在：

```text
backend/app/rag/policy_retriever.py
```

但当前规则代码使用的是 `vector_retriever.py`。

## API 响应结构

响应模型在：

```text
backend/app/schemas/review.py
backend/app/schemas/contract_fields.py
```

核心返回字段：

```text
filename
text_length
text_preview
field_extraction
finding_count
findings[]
```

每个 `finding` 包含：

```text
rule_code
status
severity
summary
contract_quote
suggestion
needs_human_review
knowledge_citations[]
```

每条 citation 可能包含：

```text
chunk_id
document_name
chapter_title
section_title
text
score
vector_score
rerank_score
```

## 常见问题

### 1. 直接运行脚本报 `No module named 'app'`

优先用模块方式：

```bash
cd backend
.venv/bin/python -m scripts.test_vector_search
```

`scripts/test_vector_search.py` 当前也已经在文件开头把 `backend/` 加入 `sys.path`，所以直接运行也可以：

```bash
.venv/bin/python scripts/test_vector_search.py
```

### 2. `use_reranker=True` 报 tokenizer 错误

典型错误：

```text
AttributeError: XLMRobertaTokenizer has no attribute prepare_for_model
```

原因是 `transformers 5.x` 与 `FlagEmbedding 1.4.0` 不兼容。按 `requirements.txt` 安装：

```bash
cd backend
.venv/bin/pip install -r requirements.txt
```

确认版本：

```bash
.venv/bin/python -c 'import importlib.metadata as m; print(m.version("FlagEmbedding")); print(m.version("transformers"))'
```

预期：

```text
1.4.0
4.57.3
```

### 3. Docker 拉取 `pgvector/pgvector:pg16` 超时

典型错误：

```text
failed to resolve reference "docker.io/pgvector/pgvector:pg16"
i/o timeout
```

这是 Docker Hub 网络问题。先单独测试：

```bash
sudo docker pull pgvector/pgvector:pg16
```

必要时配置 Docker registry mirror 或代理。

### 4. 连接 PostgreSQL 失败

检查容器：

```bash
sudo docker ps
```

检查 `backend/.env`：

```env
DATABASE_URL=postgresql+psycopg2://contract_user:contract_pass@localhost:5432/contract_review
```

检查数据库是否初始化：

```bash
cd backend
.venv/bin/python -m scripts.init_db
.venv/bin/python -m scripts.index_policy_chunks
```

### 5. Hugging Face 下载慢或提示未认证

模型首次加载时会访问 Hugging Face Hub。未设置 token 时可能出现：

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

这不是致命错误，只是可能限速。需要更稳定下载时设置 `HF_TOKEN` 或提前缓存模型。

## 推荐开发顺序

第一次启动完整项目：

```bash
cd /home/aris/contract-review-platform
sudo docker compose up -d postgres

cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m scripts.init_db
.venv/bin/python -m scripts.index_policy_chunks
.venv/bin/python scripts/test_vector_search.py
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```bash
cd /home/aris/contract-review-platform/frontend
npm run dev
```

然后访问：

```text
http://localhost:5173
```

## 当前维护备注

- 根目录 `README.md` 是项目总索引，以后优先阅读这里理解项目。
- `backend/.env` 是实际后端配置，根目录 `.env.example` 目前为空。
- `backend/.env.example` 只包含 LLM 配置，未覆盖数据库和 embedding/reranker 配置。
- `docker-data/postgres/` 是数据库数据目录，权限可能属于容器用户，不要随意编辑。
- `backend/uploads/` 是上传文件保存目录，里面已有历史测试上传文件。
- 前端 `App.tsx` 展示 `vector_score` 和 `rerank_score`，可用于确认 RAG 是否实际工作。
- 当前 git 工作区可能已有其他文件改动；维护时不要无关回滚。
