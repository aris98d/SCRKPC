# SCRKPC-0.6.0-policy-rag 项目说明文档

## 1. 项目简介

`SCRKPC-0.6.0-policy-rag` 是一个面向企业采购合同审查场景的前后端分离 Demo 项目。项目核心目标是：用户上传采购合同文件后，系统自动解析合同文本，调用本地大模型抽取合同字段，再通过规则引擎识别合同风险，并从企业采购合同管理制度知识库中检索相关制度依据，最终在前端页面展示审查结果。

这个项目可以理解为一个小型的：

```text
规则引擎 + 本地大模型 + 制度知识库检索 的采购合同审查系统原型
```

目前项目已经实现了完整的基础闭环：

```text
上传合同
  ↓
解析文本
  ↓
LLM 抽取字段
  ↓
规则发现风险
  ↓
制度知识库检索依据
  ↓
前端展示审查结果
```

需要注意的是，当前版本的 RAG 检索主要是“制度文本切分 + 关键词加权检索”，还不是完整的 `embedding + pgvector` 向量检索版本。它更适合作为项目早期原型、课程项目、企业制度审查 Demo 或后续接入向量数据库的基础版本。

---

## 2. 技术栈

### 后端

- Python
- FastAPI
- Pydantic / Pydantic Settings
- OpenAI Python SDK
- Ollama OpenAI-compatible API
- PyMuPDF：解析 PDF
- python-docx：解析 Word 文档

### 前端

- React
- TypeScript
- Vite
- Ant Design
- Axios

### 本地大模型

项目默认通过 Ollama 调用本地模型：

```text
qwen2.5:7b-instruct
```

默认服务地址：

```text
http://127.0.0.1:11434/v1
```

---

## 3. 项目目录结构

项目主目录结构如下：

```text
SCRKPC-0.6.0-policy-rag
├── backend
│   ├── app
│   │   ├── api
│   │   │   └── contracts.py
│   │   ├── core
│   │   │   └── config.py
│   │   ├── llm
│   │   │   └── client.py
│   │   ├── rag
│   │   │   ├── policy_loader.py
│   │   │   ├── policy_retriever.py
│   │   │   └── simple_retriever.py
│   │   ├── review
│   │   │   └── rules.py
│   │   ├── schemas
│   │   │   ├── contract_fields.py
│   │   │   └── review.py
│   │   ├── services
│   │   │   ├── document_parser.py
│   │   │   └── field_extractor.py
│   │   └── main.py
│   ├── requirements.txt
│   └── scripts
│       └── test_local_llm.py
├── frontend
│   ├── src
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.ts
├── sample-data
│   ├── contracts
│   │   ├── purchase_contract_01.txt
│   │   ├── purchase_contract_02.txt
│   │   ├── purchase_contract_03.txt
│   │   └── purchase_contract_04.txt
│   └── knowledge
│       └── purchase_policy.txt
├── docs
│   └── deployment
│       └── local-llm-ollama.md
├── docker-compose.yml
├── README.md
├── AGENTS.md
└── .env.example
```

可以简单理解为：

```text
frontend：负责页面上传和结果展示
backend：负责合同解析、字段抽取、规则审查、制度检索
sample-data：放测试合同和采购制度知识库
docs：放部署说明
```

---

## 4. 系统整体调用流程

系统运行时的核心调用链如下：

```text
用户在前端上传合同文件
        ↓
frontend/src/App.tsx
        ↓
POST http://127.0.0.1:8000/api/contracts/review-demo
        ↓
backend/app/api/contracts.py
        ↓
保存上传文件到 uploads/
        ↓
backend/app/services/document_parser.py
        ↓
解析 txt / docx / pdf 为纯文本
        ↓
backend/app/services/field_extractor.py
        ↓
调用本地 LLM 抽取合同字段
        ↓
backend/app/review/rules.py
        ↓
执行规则审查
        ↓
backend/app/rag/policy_retriever.py
        ↓
从 purchase_policy.txt 切分出来的制度 chunk 中检索依据
        ↓
返回 JSON 审查结果
        ↓
前端展示字段、风险项、制度依据
```

这个流程中最核心的后端链路是：

```text
contracts.py
→ document_parser.py
→ field_extractor.py
→ rules.py
→ policy_retriever.py
→ policy_loader.py
```

---

## 5. 后端文件说明

后端目录位于：

```text
backend/
```

后端使用 FastAPI 构建，主要负责合同文件接收、文本解析、字段抽取、风险审查和制度依据检索。

---

### 5.1 `backend/app/main.py`

这是后端服务入口文件。

主要作用：

1. 创建 FastAPI 应用；
2. 配置跨域 CORS；
3. 注册合同审查路由；
4. 提供健康检查接口。

核心逻辑：

```python
app = FastAPI(title="Contract Review Platform Demo")
```

前端默认运行在：

```text
http://localhost:5173
```

后端默认运行在：

```text
http://127.0.0.1:8000
```

因此 `main.py` 中配置了 CORS，允许前端跨域访问后端接口。

健康检查接口：

```text
GET /health
```

如果返回：

```json
{"status": "ok"}
```

说明后端服务启动成功。

---

### 5.2 `backend/app/api/contracts.py`

这是后端最核心的 API 文件，负责接收前端上传的合同文件并启动审查流程。

核心接口：

```text
POST /api/contracts/review-demo
```

该接口的主要流程：

1. 接收上传文件；
2. 校验文件类型；
3. 保存文件到 `uploads/`；
4. 调用文档解析模块提取文本；
5. 调用大模型抽取合同字段；
6. 调用规则引擎审查合同风险；
7. 返回完整审查结果。

允许上传的文件格式：

```text
.txt
.docx
.pdf
```

接口返回内容包括：

```text
filename：文件名
text_length：文本长度
text_preview：合同文本预览
field_extraction：字段抽取结果
finding_count：风险数量
findings：风险项列表
```

该文件可以理解为整个后端合同审查流程的“总调度中心”。

---

### 5.3 `backend/app/services/document_parser.py`

该文件负责将上传的合同文件解析为纯文本。

支持三种格式：

```text
txt
docx
pdf
```

主要函数：

#### `parse_txt`

直接读取 UTF-8 编码的 `.txt` 文件。

#### `parse_docx`

使用 `python-docx` 读取 Word 文档中的段落文本。

当前版本主要读取普通段落，不专门处理复杂表格、页眉页脚、批注等内容。

#### `parse_pdf`

使用 `PyMuPDF` 读取 PDF 文本。

解析 PDF 时，会在每页文本前加入页码标记，例如：

```text
[Page 1]
第一页文本

[Page 2]
第二页文本
```

这样后续如果要做原文定位，会更方便。

#### `parse_document`

统一入口函数，根据文件后缀自动选择解析方式。

整体作用：

```text
合同文件 → 纯文本
```

---

### 5.4 `backend/app/services/field_extractor.py`

该文件负责调用本地大模型抽取合同字段。

它不是规则审查模块，而是信息抽取模块。

当前抽取字段包括：

```text
contract_type：合同类型
party_a：甲方名称
party_b：乙方名称
amount_number：合同小写金额
amount_text：合同大写金额
payment_terms：付款条件
delivery_date：交付时间
dispute_resolution：争议解决方式
confidence：置信度
```

主要函数：

#### `build_field_extraction_prompt`

构造给大模型的提示词。

提示词要求模型：

1. 只输出 JSON；
2. 不要输出 Markdown；
3. 如果字段无法确定，填 `null`；
4. `amount_number` 只能输出纯数字；
5. `delivery_date` 即使是“双方另行协商”也要抽取原文。

这里的设计比较关键。比如合同写：

```text
交付时间：双方另行协商。
```

模型不能直接填 `null`，而应该抽取：

```json
"delivery_date": "双方另行协商"
```

因为后续规则引擎需要判断它是不是不确定表述。

#### `extract_json_from_text`

用于修复和提取模型输出中的 JSON。

有些模型可能会输出 Markdown 代码块，例如：

````markdown
```json
{
  "party_a": "某公司"
}
```
````

该函数会去掉代码块，再从文本中提取 `{...}` JSON 内容。

#### `extract_contract_fields`

字段抽取总入口。

流程：

```text
构造 prompt
  ↓
call_llm(prompt)
  ↓
提取 JSON
  ↓
Pydantic 校验
  ↓
返回 FieldExtractionResult
```

如果抽取失败，系统不会直接崩溃，而是返回：

```json
{
  "status": "failed",
  "fields": null,
  "error_message": "错误信息"
}
```

---

### 5.5 `backend/app/llm/client.py`

该文件封装本地大模型调用。

虽然代码中使用的是 OpenAI Python SDK：

```python
from openai import OpenAI
```

但实际连接的是 Ollama 提供的 OpenAI-compatible API。

默认配置：

```text
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:7b-instruct
```

核心函数：

#### `get_llm_client`

创建 OpenAI 客户端，连接本地 Ollama 服务。

#### `call_llm`

向本地模型发送合同字段抽取 prompt，并返回模型输出。

调用时设置了：

```python
temperature=0
response_format={"type": "json_object"}
```

这样可以尽量让模型稳定输出 JSON。

如果 Ollama 或模型对 `response_format` 支持不完整，可能需要从该文件排查和调整。

---

### 5.6 `backend/app/core/config.py`

该文件负责读取后端配置。

使用 `pydantic-settings` 从环境变量或 `.env` 文件读取：

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
```

默认配置：

```text
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen2.5:7b-instruct
```

文件中使用了 `@lru_cache`，表示配置只加载一次，避免重复读取。

---

### 5.7 `backend/app/schemas/contract_fields.py`

该文件定义合同字段抽取结果的数据结构。

核心模型：

#### `ContractFields`

表示抽取出的合同字段：

```text
contract_type
party_a
party_b
amount_number
amount_text
payment_terms
delivery_date
dispute_resolution
confidence
```

其中 `amount_number` 带有字段校验逻辑，可以将模型输出的字符串金额转换为数字。

例如：

```json
"amount_number": "100,000.00"
```

会被转换为：

```python
100000.0
```

#### `FieldExtractionResult`

表示字段抽取是否成功：

```text
status：success / failed
fields：抽取字段
error_message：错误信息
```

---

### 5.8 `backend/app/schemas/review.py`

该文件定义合同审查结果的数据结构。

核心模型包括：

#### `KnowledgeCitation`

表示制度依据引用。

字段包括：

```text
chunk_id：知识块 ID
document_name：制度文档名称
chapter_title：章节标题
section_title：条款标题
text：制度原文片段
score：检索相关度得分
```

#### `ReviewFinding`

表示单个合同风险项。

字段包括：

```text
rule_code：规则编号
status：审查状态
severity：风险级别
summary：风险摘要
contract_quote：合同原文
suggestion：修改建议
needs_human_review：是否需要人工复核
knowledge_citations：制度依据列表
```

#### `ReviewDemoResponse`

表示接口完整返回结果。

字段包括：

```text
filename
text_length
text_preview
field_extraction
finding_count
findings
```

---

### 5.9 `backend/app/review/rules.py`

这是当前合同风险审查的核心规则文件。

它基于正则表达式和关键词判断合同是否存在风险。目前主要检测以下几类问题：

```text
预付款比例是否超过 30%
交付日期是否不明确
争议解决地是否对甲方不利
合同金额大小写信息是否完整或一致
```

#### `review_contract`

规则审查总入口。

它会依次执行多个检查函数：

```python
checks = [
    check_prepayment_limit,
    check_delivery_date,
    check_dispute_location,
    check_amount_consistency,
]
```

每个检查函数如果发现风险，就返回一个 `ReviewFinding`。

---

#### `check_prepayment_limit`

检查预付款比例是否超过企业制度要求。

当前规则会匹配类似表达：

```text
预付款 50%
支付合同总额的50%
合同签订后支付50%
```

如果识别到比例大于 30%，就返回高风险，并调用制度检索：

```python
search_policy_evidence(
    rule_code="PAYMENT_PREPAYMENT_LIMIT",
    query="采购合同 预付款比例 超过30% 专项审批",
    top_k=3,
)
```

返回的制度依据会展示在前端。

---

#### `check_delivery_date`

检查交付日期是否存在不确定表述。

当前风险词包括：

```text
另行协商
待定
双方协商确定
```

如果合同中同时出现“交付/交货”和上述风险词，则判定交付日期不明确。

---

#### `check_dispute_location`

检查争议解决地是否不符合企业制度。

当前主要识别：

```text
乙方所在地法院
乙方所在地人民法院
```

如果合同约定由乙方所在地法院管辖，就会提示风险，并建议改为甲方所在地人民法院。

---

#### `check_amount_consistency`

检查合同金额大小写是否完整或一致。

它会尝试提取：

```text
小写金额
中文大写金额
```

目前小写金额提取已经实现，但中文大写金额转换还没有完全实现。因此当前版本经常会返回：

```text
合同金额大小写信息不完整，无法自动核验
```

这是后续非常值得优先完善的部分。

---

### 5.10 `backend/app/rag/policy_loader.py`

该文件负责读取并切分采购合同管理制度文本。

制度文件位置：

```text
sample-data/knowledge/purchase_policy.txt
```

它会把一整份 Markdown 制度文本按照标题和条款切成多个 chunk。

例如：

```markdown
## 第四章 预付款管理

### 第十一条 预付款比例控制原则

采购合同约定预付款的，应严格控制预付款比例。
```

会被切分为：

```json
{
  "chunk_id": "purchase_policy_0011",
  "document_name": "采购合同管理制度",
  "chapter_title": "第四章 预付款管理",
  "section_title": "第十一条 预付款比例控制原则",
  "text": "采购合同约定预付款的，应严格控制预付款比例..."
}
```

这个文件的作用是：

```text
制度原文 → 结构化知识块 chunks
```

---

### 5.11 `backend/app/rag/policy_retriever.py`

该文件负责从制度 chunks 中检索相关制度依据。

当前检索方式是关键词加权检索，而不是向量检索。

核心配置是 `RULE_KEYWORDS`，它定义了每个规则编号对应的关键词。

例如：

```python
"PAYMENT_PREPAYMENT_LIMIT": [
    "预付款",
    "30%",
    "专项审批",
    "合同总金额",
    "部门负责人",
    "法务负责人",
]
```

核心检索函数：

```python
search_policy_evidence(query=None, rule_code=None, top_k=3)
```

打分规则：

```text
关键词命中正文 text：+2 分
关键词命中条款标题 section_title：+3 分
关键词命中章节标题 chapter_title：+1 分
```

最后按得分从高到低排序，返回前 `top_k` 条制度依据。

返回结果会作为 `knowledge_citations` 附加到风险项中。

---

### 5.12 `backend/app/rag/simple_retriever.py`

这是一个更早期或备用的简单检索器。

它的切分和检索能力比 `policy_retriever.py` 弱，主要按行和关键词匹配。

当前正式审查流程中主要使用的是：

```text
policy_retriever.py
```

因此 `simple_retriever.py` 可以暂时理解为实验代码或备用代码。

---

### 5.13 `backend/scripts/test_local_llm.py`

该脚本用于测试本地 Ollama 大模型是否可用。

它会直接调用：

```text
http://localhost:11434/v1
```

并向本地模型发送一段测试合同，让模型尝试抽取字段。

如果该脚本能正常返回 JSON，说明本地模型服务基本配置成功。

---

## 6. 前端文件说明

前端目录位于：

```text
frontend/
```

前端使用 Vite + React + TypeScript + Ant Design 构建。

---

### 6.1 `frontend/package.json`

该文件定义前端依赖和启动命令。

主要依赖：

```text
react：页面框架
react-dom：React DOM 渲染
antd：UI 组件库
axios：请求后端接口
vite：前端开发服务器和构建工具
typescript：类型检查
```

常用命令：

```bash
npm install
npm run dev
npm run build
```

---

### 6.2 `frontend/src/main.tsx`

前端入口文件。

它负责把 `App.tsx` 渲染到页面中的：

```html
<div id="root"></div>
```

---

### 6.3 `frontend/src/App.tsx`

这是前端最核心的页面文件。

主要负责：

1. 选择并上传合同文件；
2. 调用后端审查接口；
3. 展示合同字段抽取结果；
4. 展示风险项；
5. 展示制度依据。

核心状态：

```tsx
const [fileList, setFileList] = useState<UploadFile[]>([]);
const [result, setResult] = useState<ReviewResponse | null>(null);
const [loading, setLoading] = useState(false);
```

含义：

```text
fileList：当前选择的合同文件
result：后端返回的审查结果
loading：是否正在审查中
```

上传逻辑使用 Ant Design 的 `Upload` 组件。

其中：

```tsx
beforeUpload={() => false}
```

表示不让 Ant Design 自动上传，而是点击按钮后手动调用接口。

后端请求地址：

```text
http://127.0.0.1:8000/api/contracts/review-demo
```

前端展示的内容主要包括：

```text
文件名
文本长度
风险数量
字段抽取结果
风险列表
制度依据 citations
```

---

### 6.4 `frontend/src/App.css` 和 `frontend/src/index.css`

这两个文件主要负责页面样式。

`App.css` 更偏向具体页面组件布局；

`index.css` 更偏向全局样式。

---

## 7. 数据文件说明

数据目录位于：

```text
sample-data/
```

包含测试合同和制度知识库。

---

### 7.1 `sample-data/knowledge/purchase_policy.txt`

这是项目的企业制度知识库文本。

内容是一份完整的《采购合同管理制度》，包括：

```text
总则
职责分工
采购合同订立要求
预付款管理
交付与验收条款管理
合同金额管理
付款条款管理
发票与税务条款管理
争议解决条款管理
合同审批管理
合同签署管理
合同履行管理
合同变更、解除与补充协议
合同归档管理
监督检查与责任追究
附件一：采购合同重点审核清单
附件二：采购合同推荐条款示例
```

它是制度依据检索的来源。

调用关系：

```text
purchase_policy.txt
  ↓
policy_loader.py 切分为 chunks
  ↓
policy_retriever.py 检索相关制度依据
  ↓
rules.py 将制度依据附加到风险项
  ↓
前端展示制度引用
```

---

### 7.2 `sample-data/contracts/purchase_contract_01.txt`

这是一份明显有风险的测试采购合同。

典型风险包括：

```text
预付款比例为 50%，超过制度 30% 要求
交付时间写为“双方另行协商”
争议解决地为乙方所在地法院
金额大小写可能不一致或无法核验
```

适合用来测试系统是否能识别基本规则风险。

---

### 7.3 `sample-data/contracts/purchase_contract_02.txt`

这是一份相对规范的采购合同样例。

典型内容包括：

```text
合同金额较规范
交付时间明确
预付款比例为 30%
争议解决地为甲方所在地人民法院
```

适合用来测试正常合同或低风险合同场景。

由于当前中文大写金额解析还不完善，该合同仍可能出现“金额大小写信息不完整，无法自动核验”的提示。

---

### 7.4 `sample-data/contracts/purchase_contract_03.txt`

这是一份新媒体营销合作协议样例。

其中包含一些潜在不公平条款或高风险条款，例如：

```text
甲方可随时单方面终止
乙方承担所有延误责任
违约金比例过高
争议解决地设置异常
```

不过当前规则引擎尚未覆盖这些风险，因此该合同更适合作为后续扩展规则的测试样本。

---

### 7.5 `sample-data/contracts/purchase_contract_04.txt`

这是一份软件系统定制开发合同样例。

其中可能存在：

```text
知识产权归属冲突
源代码权属表述矛盾
验收标准过度依赖乙方单方测试报告
```

当前规则引擎尚未覆盖知识产权冲突、验收权缺失、源代码交付冲突等风险，后续可以基于该样例扩展规则。

---

## 8. 本地运行方式

### 8.1 准备 Ollama 本地大模型

安装 Ollama 后，拉取模型：

```bash
ollama pull qwen2.5:7b-instruct
```

确认 Ollama 服务运行在：

```text
http://127.0.0.1:11434
```

项目默认使用 OpenAI-compatible endpoint：

```text
http://127.0.0.1:11434/v1
```

---

### 8.2 启动后端

进入后端目录：

```bash
cd backend
```

创建并激活虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```bash
.venv\Scripts\Activate.ps1
```

Linux / macOS：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动 FastAPI：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

测试后端是否启动成功：

```text
http://127.0.0.1:8000/health
```

如果返回：

```json
{"status": "ok"}
```

说明后端正常。

---

### 8.3 启动前端

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务器：

```bash
npm run dev
```

默认访问地址：

```text
http://localhost:5173
```

---

## 9. API 说明

### 9.1 健康检查

```text
GET /health
```

返回示例：

```json
{
  "status": "ok"
}
```

---

### 9.2 合同审查接口

```text
POST /api/contracts/review-demo
```

请求类型：

```text
multipart/form-data
```

参数：

```text
file：合同文件，支持 .txt / .docx / .pdf
```

返回示例结构：

```json
{
  "filename": "purchase_contract_01.txt",
  "text_length": 354,
  "text_preview": "合同文本预览...",
  "field_extraction": {
    "status": "success",
    "fields": {
      "contract_type": "采购合同",
      "party_a": "甲方公司",
      "party_b": "乙方公司",
      "amount_number": 100000,
      "amount_text": "人民币壹拾万元整",
      "payment_terms": "合同签订后支付合同总额的50%",
      "delivery_date": "双方另行协商",
      "dispute_resolution": "乙方所在地法院",
      "confidence": 0.9
    },
    "error_message": null
  },
  "finding_count": 3,
  "findings": [
    {
      "rule_code": "PAYMENT_PREPAYMENT_LIMIT",
      "status": "risk",
      "severity": "high",
      "summary": "预付款比例超过制度要求",
      "contract_quote": "合同签订后支付合同总额的50%",
      "suggestion": "建议将预付款比例控制在30%以内，超过30%的应提交专项审批。",
      "needs_human_review": true,
      "knowledge_citations": [
        {
          "chunk_id": "purchase_policy_0011",
          "document_name": "采购合同管理制度",
          "chapter_title": "第四章 预付款管理",
          "section_title": "第十一条 预付款比例控制原则",
          "text": "采购合同预付款比例原则上不得超过合同总金额的30%...",
          "score": 16
        }
      ]
    }
  ]
}
```

---

## 10. 当前已实现能力

当前版本已经实现：

```text
前端合同上传
后端文件接收
支持 txt / docx / pdf 文本解析
本地 LLM 合同字段抽取
采购合同规则审查
制度文本切分
制度依据关键词检索
审查结果前端展示
制度依据 citations 展示
```

当前重点规则包括：

```text
预付款比例超过 30%
交付日期不明确
争议解决地为乙方所在地
合同金额大小写信息不完整或无法核验
```

---

## 11. 当前局限性

### 11.1 当前 RAG 不是向量数据库版

当前制度检索逻辑主要是关键词匹配：

```python
if keyword in text:
    score += 2
```

它不是完整的：

```text
embedding + pgvector + 相似度检索
```

因此对于同义表达、隐含语义、改写句式的召回能力有限。

例如：

```text
先付一半钱
```

语义上接近：

```text
预付款比例为 50%
```

但关键词检索不一定能稳定召回相关制度条款。

---

### 11.2 中文大写金额解析未完全实现

当前小写金额提取已经具备基础能力，但中文大写金额转换还不完善。

因此金额一致性检查目前仍偏弱，容易返回：

```text
合同金额大小写信息不完整，无法自动核验
```

后续应重点完善中文金额转数字逻辑。

---

### 11.3 发票税率规则尚未完整接入

制度检索中已经存在：

```text
INVOICE_TAX_MISSING
```

但规则引擎中尚未完整实现对应的：

```text
check_invoice_tax_missing
```

因此合同缺少发票类型、税率、含税状态时，当前版本可能不会自动识别。

---

### 11.4 复杂合同风险尚未覆盖

当前规则主要覆盖基础采购合同风险，尚未覆盖：

```text
霸王条款
单方解除权
过高违约金
知识产权归属冲突
验收权缺失
源代码交付冲突
数据安全和保密义务
自动续约和自动扣费
供应商责任限制条款
```

这些可以作为后续扩展方向。

---

## 12. 后续扩展建议

### 12.1 升级为 pgvector 向量 RAG

后续可以将当前关键词检索升级为向量检索：

```text
purchase_policy.txt
  ↓
policy_loader.py 切分 chunk
  ↓
embedding 模型向量化
  ↓
存入 PostgreSQL + pgvector
  ↓
合同风险 query 向量化
  ↓
向量相似度检索
  ↓
返回相关制度依据
```

这样可以提升语义检索能力。

---

### 12.2 增加更多审查规则

建议增加以下规则：

```text
INVOICE_TAX_MISSING：发票类型、税率、含税状态缺失
UNILATERAL_TERMINATION_RISK：单方解除风险
EXCESSIVE_LIQUIDATED_DAMAGES：违约金过高
IP_OWNERSHIP_CONFLICT：知识产权归属冲突
ACCEPTANCE_RIGHT_MISSING：验收权缺失
SOURCE_CODE_DELIVERY_CONFLICT：源代码交付冲突
CONFIDENTIALITY_MISSING：保密条款缺失
AUTO_RENEWAL_RISK：自动续约风险
SUPPLIER_LIABILITY_LIMITATION：供应商责任限制风险
```

---

### 12.3 完善中文大写金额识别

建议实现：

```text
人民币壹拾万元整 → 100000
人民币壹拾伍万元整 → 150000
人民币叁拾贰万伍仟元整 → 325000
```

这样才能真正完成金额大小写一致性检查。

---

### 12.4 增强前端错误提示

当前前端可以增加更友好的错误提示，例如：

```text
后端服务未启动
Ollama 模型未启动
文件格式不支持
LLM 字段抽取失败
合同文本为空
```

这样用户体验会更好。

---

### 12.5 增加数据库和审查历史

后续可以加入数据库，保存：

```text
上传合同记录
字段抽取结果
风险审查结果
制度依据引用
人工复核意见
审查报告导出记录
```

这样系统会更接近真实企业合同审查平台。

---

## 13. 项目核心文件速查表

| 文件 | 作用 |
|---|---|
| `backend/app/main.py` | FastAPI 后端入口，注册路由和 CORS |
| `backend/app/api/contracts.py` | 合同审查接口，总调度文件 |
| `backend/app/services/document_parser.py` | 解析 txt / docx / pdf 为纯文本 |
| `backend/app/services/field_extractor.py` | 调用本地 LLM 抽取合同字段 |
| `backend/app/llm/client.py` | 封装 Ollama / OpenAI-compatible 模型调用 |
| `backend/app/review/rules.py` | 合同风险规则审查 |
| `backend/app/rag/policy_loader.py` | 读取并切分采购制度文本 |
| `backend/app/rag/policy_retriever.py` | 根据规则和关键词检索制度依据 |
| `backend/app/schemas/contract_fields.py` | 合同字段抽取结果模型 |
| `backend/app/schemas/review.py` | 合同审查结果模型 |
| `frontend/src/App.tsx` | 前端上传、请求、展示主页面 |
| `sample-data/knowledge/purchase_policy.txt` | 采购合同管理制度知识库 |
| `sample-data/contracts/*.txt` | 测试采购合同样例 |

---

## 14. 一句话总结

`SCRKPC-0.6.0-policy-rag` 是一个采购合同智能审查原型系统。它通过 FastAPI 接收合同文件，通过本地大模型抽取关键字段，通过规则引擎识别合同风险，并从企业采购合同管理制度中检索相关依据，最终由 React 前端展示审查结论、合同原文片段、修改建议和制度引用。

当前版本适合用于演示合同审查系统的基本架构，也适合作为后续扩展 pgvector 向量知识库、更多规则审查、审查报告导出和企业级合同管理平台的基础骨架。
