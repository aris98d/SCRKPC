from openai import OpenAI


client = OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1",
)

response = client.chat.completions.create(
    model="qwen2.5:7b-instruct",
    messages=[
        {
            "role": "system",
            "content": "你是一个合同字段抽取助手，只输出JSON。",
        },
        {
            "role": "user",
            "content": """
请从下面合同中抽取甲方、乙方、金额、付款方式，只输出JSON。

采购合同
甲方：长沙某某科技有限公司
乙方：湖南某某设备有限公司
合同金额：人民币100000元，大写人民币壹拾贰万元整。
付款方式：合同签订后支付合同总额的50%。
""",
        },
    ],
    temperature=0,
)

print(response.choices[0].message.content)