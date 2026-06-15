from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
POLICY_PATH = PROJECT_ROOT / "sample-data" / "knowledge" / "purchase_policy.txt"


def load_policy_text() -> str:
    if not POLICY_PATH.exists():
        raise FileNotFoundError(f"Policy file not found: {POLICY_PATH}")

    return POLICY_PATH.read_text(encoding="utf-8")


def clean_heading(line: str, prefix: str) -> str:
    return line.replace(prefix, "", 1).strip()


def split_policy_into_chunks(policy_text: str) -> list[dict]:
    """
    按制度文档的真实层级切分：

    # 采购合同管理制度                  -> 文档标题，不作为 chunk
    ## 第四章 预付款管理               -> chapter_title
    ### 第十一条 预付款比例控制原则     -> section_title
    # 附件一：采购合同重点审核清单       -> chapter_title
    ## 一、预付款审核                  -> section_title
    # 附件二：采购合同推荐条款示例       -> chapter_title
    ## 一、预付款条款示例              -> section_title
    """

    lines = policy_text.splitlines()

    chunks: list[dict] = []

    document_name = "采购合同管理制度"
    current_chapter = ""
    current_section = ""
    current_lines: list[str] = []

    def flush_chunk() -> None:
        nonlocal current_lines

        text = "\n".join(current_lines).strip()
        if not text:
            current_lines = []
            return

        chunk_id = f"purchase_policy_{len(chunks) + 1:04d}"

        chunks.append(
            {
                "chunk_id": chunk_id,
                "document_name": document_name,
                "chapter_title": current_chapter or document_name,
                "section_title": current_section or current_chapter or document_name,
                "text": text,
            }
        )

        current_lines = []

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if line == "---":
            continue

        # 一级标题
        if line.startswith("# ") and not line.startswith("## "):
            heading = clean_heading(line, "# ")

            # 文档总标题，不生成 chunk
            if heading == document_name:
                continue

            # 附件标题，例如：附件一：采购合同重点审核清单
            flush_chunk()
            current_chapter = heading
            current_section = ""
            continue

        # 二级标题
        if line.startswith("## ") and not line.startswith("### "):
            heading = clean_heading(line, "## ")

            flush_chunk()

            # 正文章节：第几章
            if heading.startswith("第") and "章" in heading:
                current_chapter = heading
                current_section = ""
            else:
                # 附件下的小节：一、预付款审核
                current_section = heading

            continue

        # 三级标题：制度条款
        if line.startswith("### "):
            heading = clean_heading(line, "### ")

            flush_chunk()
            current_section = heading
            continue

        current_lines.append(line)

    flush_chunk()

    return chunks


def build_policy_chunks() -> list[dict]:
    text = load_policy_text()
    return split_policy_into_chunks(text)