import { useState } from "react";
import axios from "axios";
import { Button, Card, Upload, Typography, Alert, Space, Tag } from "antd";
import type { UploadFile } from "antd";

const { Title, Paragraph } = Typography;

type Finding = {
  rule_code: string;
  status: string;
  severity: string;
  summary: string;
  contract_quote?: string;
  suggestion: string;
  needs_human_review: boolean;
};

type ReviewResponse = {
  filename: string;
  text_length: number;
  text_preview: string;
  finding_count: number;
  findings: Finding[];
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
              </Card>
            ))}
          </Space>
        </Card>
      )}
    </div>
  );
}

export default App;