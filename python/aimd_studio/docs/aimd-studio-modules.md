# AIMD Studio Python 模块架构

## 模块结构

```
aimd_studio/                    # 主模块
├── __init__.py                 # 入口，re-export airalogy SDK
├── export/                     # 📊 数据导出
│   ├── __init__.py
│   ├── base.py                 # 导出器基类
│   ├── json.py                 # JSON 导出
│   ├── csv.py                  # CSV 导出
│   ├── excel.py                # Excel 导出 (需要 openpyxl)
│   ├── pdf.py                  # PDF 导出 (需要 weasyprint)
│   └── html.py                 # HTML 导出
└── ai/                         # 🤖 AI 辅助
    ├── __init__.py
    ├── providers.py            # AI Provider 抽象层
    └── assistant.py            # AI 助手功能

airalogy_mock/                  # 本地服务
├── __init__.py
├── client.py                   # 本地文件/记录存储
├── server.py                   # HTTP API 服务
└── __main__.py                 # 启动入口
```

---

## 📊 数据导出模块

### 支持格式

| 格式 | 依赖 | 用途 |
|------|------|------|
| JSON | 无 | 结构化数据交换 |
| CSV | 无 | 表格数据，Excel 兼容 |
| Excel | openpyxl | 多 Sheet 工作簿 |
| PDF | weasyprint | 正式实验报告 |
| HTML | 无 | 静态网页预览 |

### 使用示例

```python
from aimd_studio.export import export_json, export_csv, export_excel, export_html
from aimd_studio.export.base import ExportConfig

data = {
    "operator": "张三",
    "temperature": 37.0,
    "measurements": [
        {"well": "A1", "od_value": 0.5},
        {"well": "A2", "od_value": 0.8},
    ]
}

# JSON 导出
result = export_json(data)
print(result.output_bytes.decode())

# CSV 导出表格数据
result = export_csv(data, table_field="measurements")

# Excel 导出 (自动创建多个 Sheet)
result = export_excel(data, output_path="report.xlsx")

# HTML 导出 (带样式)
config = ExportConfig(
    title="CCK-8 实验报告",
    author="张三",
    date="2024-12-25",
)
result = export_html(data, config=config)
```

### HTTP API

```bash
# 导出为 JSON
curl -X POST http://localhost:4000/api/export \
  -H "Content-Type: application/json" \
  -d '{"data": {...}, "format": "json"}'

# 导出为 Excel
curl -X POST http://localhost:4000/api/export \
  -H "Content-Type: application/json" \
  -d '{"data": {...}, "format": "excel"}' \
  --output report.xlsx
```

---

## 🤖 AI 辅助模块

### 支持的 AI Provider

| Provider | 环境变量 | 默认模型 |
|----------|----------|----------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini |
| Gemini | `GEMINI_API_KEY` | gemini-2.0-flash |
| Claude | `ANTHROPIC_API_KEY` | claude-3-5-sonnet |

### 功能列表

1. **suggest_next_step** - 建议下一步操作
2. **generate_description** - 为变量生成标题和描述
3. **detect_anomalies** - 检测数据异常
4. **generate_summary** - 生成实验报告摘要
5. **chat** - 通用对话

### 使用示例

```python
import asyncio
from aimd_studio.ai import AIAssistant, OpenAIProvider

async def main():
    # 使用 OpenAI
    assistant = AIAssistant(OpenAIProvider(api_key="sk-..."))
    
    # 建议下一步
    suggestion = await assistant.suggest_next_step(
        current_step="细胞接种完成",
        completed_steps=["准备培养基", "细胞计数"],
        context={"cell_density": 5000, "plate_type": "96孔板"}
    )
    print(suggestion)
    
    # 生成变量描述
    desc = await assistant.generate_description(
        var_name="seeding_density",
        var_type="int",
        context={"experiment_type": "CCK-8"}
    )
    print(desc)  # {"title": "接种密度", "description": "..."}
    
    # 检测异常
    anomalies = await assistant.detect_anomalies(
        data={"temperature": 45.0, "od_value": -0.1},
        expected_ranges={"temperature": (35, 40), "od_value": (0, 4)}
    )
    print(anomalies)

asyncio.run(main())
```

### HTTP API

```bash
# AI 对话
curl -X POST http://localhost:4000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何优化 CCK-8 实验的孵育时间？",
    "provider": "openai",
    "api_key": "sk-..."
  }'

# 建议下一步
curl -X POST http://localhost:4000/api/ai/suggest-next-step \
  -H "Content-Type: application/json" \
  -d '{
    "current_step": "加入 CCK-8 试剂",
    "completed_steps": ["细胞接种", "药物处理"],
    "context": {"treatment_time": 48}
  }'

# 生成变量描述
curl -X POST http://localhost:4000/api/ai/generate-description \
  -H "Content-Type: application/json" \
  -d '{
    "var_name": "inhibition_rate",
    "var_type": "float"
  }'

# 检测异常
curl -X POST http://localhost:4000/api/ai/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"temperature": 45.0, "od_value": -0.1},
    "expected_ranges": {"temperature": [35, 40], "od_value": [0, 4]}
  }'
```

---

## 安装依赖

```bash
# 基础依赖
pip install git+https://github.com/airalogy/airalogy.git
pip install fastapi uvicorn

# 导出功能 (可选)
pip install openpyxl    # Excel 导出
pip install weasyprint  # PDF 导出

# AI 功能 (httpx 已包含在 airalogy 依赖中)
# 只需配置 API Key 环境变量
```

---

## 启动服务

```bash
python -m airalogy_mock
```

服务启动后访问 http://localhost:4000/docs 查看完整 API 文档。
