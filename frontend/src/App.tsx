import { useState } from "react";
import axios from "axios";
import { Button, Card, Upload, Typography, Alert, Space, Tag, Descriptions, Empty } from "antd";
import type { UploadFile } from "antd";

const { Title, Paragraph } = Typography;

// ...你的 Type 定义保持不变...

function App() {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleReview = async () => {
    if (fileList.length === 0 || !fileList[0].originFileObj) return;

    const formData = new FormData();
    formData.append("file", fileList[0].originFileObj);
    setLoading(true);

    try {
      const response = await axios.post<ReviewResponse>(
        "http://127.0.0.1:8000/api/contracts/review-demo",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(response.data);
    } catch (error) {
      console.error("审查请求失败:", error);
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
          <Title level={3}>审查报表汇总</Title>
          <Descriptions bordered size="small" column={3} style={{ marginBottom: 16 }}>
            <Descriptions.Item label="文件名">{result.filename}</Descriptions.Item>
            <Descriptions.Item label="文本长度">{result.text_length} 字</Descriptions.Item>
            <Descriptions.Item label="风险数量">
              <Tag color={result.finding_count > 0 ? "red" : "green"}>{result.finding_count} 个</Tag>
            </Descriptions.Item>
          </Descriptions>

          <Alert
            message={`共发现 ${result.finding_count} 个合规风险项`}
            type={result.finding_count > 0 ? "warning" : "success"}
            showIcon
            style={{ marginBottom: 24 }}
          />

          {/* ===== 核心修复与升级：合同字段抽取板块 ===== */}
          <Card type="inner" title="📦 核心合同核心要素抽取" style={{ marginTop: 24, background: "#fafafa" }}>
            {result.field_extraction && result.field_extraction.fields ? (
              <Descriptions bordered column={2} size="small" bg="#fff">
                <Descriptions.Item label="合同类型">
                  <Tag color="blue">{result.field_extraction.fields.contract_type || "未识别"}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="AI 置信度">
                  {(result.field_extraction.fields.confidence * 100).toFixed(1)}%
                </Descriptions.Item>
                <Descriptions.Item label="甲方（招采方）">
                  <strong>{result.field_extraction.fields.party_a || "未知"}</strong>
                </Descriptions.Item>
                <Descriptions.Item label="乙方（供应方）">
                  <strong>{result.field_extraction.fields.party_b || "未知"}</strong>
                </Descriptions.Item>
                <Descriptions.Item label="小写金额（元）">
                  {result.field_extraction.fields.amount_number?.toLocaleString() || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="大写金额">
                  {result.field_extraction.fields.amount_text || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="交付/履行时间" span={2}>
                  {result.field_extraction.fields.delivery_date || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="付款条款" span={2}>
                  {result.field_extraction.fields.payment_terms || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="争议解决方式" span={2}>
                  {result.field_extraction.fields.dispute_resolution || "—"}
                </Descriptions.Item>
              </Descriptions>
            ) : (
              <Empty 
                description={result.field_extraction?.error_message || "模型未能在合同中提取出有效的结构化要素"} 
                image={Empty.PRESENTED_IMAGE_SIMPLE} 
              />
            )}
          </Card>

          {/* ===== 风险项列表板块 ===== */}
          <Title level={4} style={{ marginTop: 32 }}>⚠️ 详细风险项审查清单</Title>
          <Space direction="vertical" style={{ width: "100%" }}>
            {result.findings.map((finding) => (
              <Card key={finding.rule_code} size="small" hoverable>
                <Space style={{ marginBottom: 8 }}>
                  <Tag color={finding.severity === "high" ? "red" : "orange"}>
                    {finding.severity.toUpperCase()} 风险
                  </Tag>
                  <Tag color="purple">{finding.status}</Tag>
                  <strong style={{ fontSize: 15 }}>{finding.rule_code}</strong>
                </Space>

                <Paragraph style={{ margin: "8px 0", color: "#555" }}>
                  <strong>漏洞概述：</strong>{finding.summary}
                </Paragraph>

                {finding.contract_quote && (
                  <div style={{ background: "#fffbe6", padding: "8px 12px", borderRadius: 4, margin: "8px 0", borderLeft: "4px solid #ffe58f" }}>
                    <Paragraph style={{ margin: 0, fontStyle: "italic" }}>
                      <strong>合同原文：</strong>“ {finding.contract_quote} ”
                    </Paragraph>
                  </div>
                )}

                <Paragraph style={{ margin: "8px 0 0 0", color: "#1d2129" }}>
                  <span style={{ color: "#52c41a" }}><strong>💡 整改建议：</strong></span>
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