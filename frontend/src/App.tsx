import { useState } from "react";
import axios from "axios";
import { Button, Card, Upload, Typography, Alert, Space, Tag } from "antd";
import type { UploadFile } from "antd";

const { Title, Paragraph } = Typography;

type KnowledgeCitation = {
  chunk_id: string;
  document_name: string;
  chapter_title?: string | null;
  section_title?: string | null;
  text: string;
  score?: number | null;
  vector_score?: number | null;
  rerank_score?: number | null;
};

type Finding = {
  rule_code: string;
  status: string;
  severity: string;
  summary: string;
  contract_quote?: string | null;
  suggestion: string;
  needs_human_review: boolean;
  knowledge_citations?: KnowledgeCitation[];
};

type ReviewResponse = {
  filename: string;
  text_length: number;
  text_preview: string;
  field_extraction: FieldExtraction;
  finding_count: number;
  findings: Finding[];
};

type ContractFields = {
  contract_type?: string | null;
  party_a?: string | null;
  party_b?: string | null;
  amount_number?: number | null;
  amount_text?: string | null;
  payment_terms?: string | null;
  delivery_date?: string | null;
  dispute_resolution?: string | null;
  confidence: number;
};

type FieldExtraction = {
  status: string;
  fields: ContractFields | null;
  error_message?: string | null;
};

function App() {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleReview = async () => {
    if (fileList.length === 0 || !fileList[0].originFileObj) {
      return;
    }

    const formData = new FormData();
    formData.append("file", fileList[0].originFileObj);

    setLoading(true);

    try {
      const response = await axios.post<ReviewResponse>(
        "http://127.0.0.1:8000/api/contracts/review-demo",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResult(response.data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: "40px auto", padding: 24 }}>
      <Title level={2}>企业合同智能审查 Demo</Title>

      <Card>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Upload
            beforeUpload={() => false}
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList.slice(-1))}
            accept=".txt,.docx,.pdf"
          >
            <Button>选择合同文件</Button>
          </Upload>

          <Button type="primary" loading={loading} onClick={handleReview}>
            上传并审查
          </Button>
        </Space>
      </Card>

      {result && (
        <Card style={{ marginTop: 24 }}>
          <Title level={4}>审查结果</Title>

          <Paragraph>文件名：{result.filename}</Paragraph>
          <Paragraph>文本长度：{result.text_length}</Paragraph>
          <Paragraph>发现风险数量：{result.finding_count}</Paragraph>

          <Alert
            message={`共发现 ${result.finding_count} 个风险项`}
            type={result.finding_count > 0 ? "warning" : "success"}
            showIcon
          />

          {result.field_extraction.fields && (
            <Card style={{ marginTop: 24 }}>
              <Title level={4}>合同字段抽取</Title>

              <Paragraph>
                合同类型：{result.field_extraction.fields.contract_type}
              </Paragraph>
              <Paragraph>
                甲方：{result.field_extraction.fields.party_a}
              </Paragraph>
              <Paragraph>
                乙方：{result.field_extraction.fields.party_b}
              </Paragraph>
              <Paragraph>
                小写金额：{result.field_extraction.fields.amount_number}
              </Paragraph>
              <Paragraph>
                大写金额：{result.field_extraction.fields.amount_text}
              </Paragraph>
              <Paragraph>
                付款方式：{result.field_extraction.fields.payment_terms}
              </Paragraph>
              <Paragraph>
                交付时间：{result.field_extraction.fields.delivery_date}
              </Paragraph>
              <Paragraph>
                争议解决：
                {result.field_extraction.fields.dispute_resolution}
              </Paragraph>
              <Paragraph>
                置信度：{result.field_extraction.fields.confidence}
              </Paragraph>
            </Card>
          )}

          <Title level={4} style={{ marginTop: 24 }}>
            风险项
          </Title>

          <Space direction="vertical" style={{ width: "100%" }}>
            {result.findings.map((finding) => (
              <Card key={finding.rule_code} size="small">
                <Space>
                  <Tag color={finding.severity === "high" ? "red" : "orange"}>
                    {finding.severity}
                  </Tag>
                  <strong>{finding.rule_code}</strong>
                </Space>

                <Paragraph style={{ marginTop: 12 }}>
                  {finding.summary}
                </Paragraph>

                {finding.contract_quote && (
                  <Paragraph>
                    <strong>原文：</strong>
                    {finding.contract_quote}
                  </Paragraph>
                )}

                <Paragraph>
                  <strong>建议：</strong>
                  {finding.suggestion}
                </Paragraph>

                {finding.knowledge_citations && finding.knowledge_citations.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <strong>制度依据：</strong>

                    <Space direction="vertical" style={{ width: "100%", marginTop: 8 }}>
                      {finding.knowledge_citations.map((citation) => (
                        <Card
                          key={citation.chunk_id}
                          size="small"
                          style={{ background: "#fafafa" }}
                        >
                          <Paragraph style={{ marginBottom: 8 }}>
                            <strong>{citation.document_name}</strong>
                            {citation.chapter_title && (
                              <span>｜{citation.chapter_title}</span>
                            )}
                            {citation.section_title && (
                              <span>｜{citation.section_title}</span>
                            )}
                            {citation.score !== undefined && citation.score !== null && (
                              <span>｜相关度：{citation.score}</span>
                            )}
                            {citation.rerank_score !== undefined && citation.rerank_score !== null && (
                              <span>｜重排分：{citation.rerank_score.toFixed(2)}</span>
                            )}
                            {citation.vector_score !== undefined && citation.vector_score !== null && (
                              <span>｜向量分：{citation.vector_score.toFixed(2)}</span>
                            )}
                          </Paragraph>

                          <Paragraph style={{ marginBottom: 0 }}>
                            {citation.text}
                          </Paragraph>
                        </Card>
                      ))}
                    </Space>
                  </div>
                )}
              </Card>
            ))}
          </Space>
        </Card>
      )}
    </div>
  );
}

export default App;
