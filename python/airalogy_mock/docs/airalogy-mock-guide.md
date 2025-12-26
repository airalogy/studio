# Airalogy Mock Server 使用指南

本地模拟 Airalogy Platform API，用于 AIMD Studio 开发测试。

## 快速开始

### 启动服务器

```bash
# 方式 1: 模块启动
python -m airalogy_mock

# 方式 2: uvicorn 启动 (支持热重载)
uvicorn airalogy_mock.server:app --reload --port 4000
```

服务器启动后：
- API 端点: http://localhost:4000
- API 文档: http://localhost:4000/docs

### 本地存储

数据存储在 `.airalogy_mock/` 目录：
- `files/` - 上传的文件
- `records/` - Record JSON 文件

## Record 模式

Record 模式用于记录完整的实验数据，生成标准的 Airalogy Record JSON 格式。

### Python 客户端使用

```python
from airalogy_mock import Airalogy

client = Airalogy()

# 启动 Record Session
session = client.start_record_session(
    protocol_id="quantum_cck8",
    lab_id="starfleet",
    project_id="prometheus",
    protocol_version="2.0.0",
)

# 设置变量
session.set_var("operator", "airalogy.id.user.alice")
session.set_var("mission_code", "PRO-2024-001")
session.set_vars({
    "culture_temp": 37.0,
    "co2_level": 5.0,
    "stability_field": 99.5,
})

# 设置表格数据
session.set_var("research_team", [
    {"name": "艾丽卡·陈", "species": "人类", "clearance_level": 7},
    {"name": "泽克斯-7", "species": "仿生人", "clearance_level": 5},
])

# 完成步骤
session.complete_step("open_portal", annotation="维度传送门已校准")
session.set_step("collect_cells", checked=None)  # 非检查项

# 通过检查点
session.pass_check("dimension_stability", annotation="维度裂隙稳定")
session.pass_check("containment_field", annotation="防护力场已激活")

# 上传文件并关联到变量
result = client.upload_file_bytes("cell_photo.png", photo_bytes)
session.set_var("cell_initial_photo", result["id"])

# 保存 Record
record_id = session.save()
print(f"Saved: {record_id}")

# 查看生成的 Record
print(session.to_json())

# 结束 Session
client.end_record_session(save=True)
```

### HTTP API 使用

```bash
# 启动 Record Session
curl -X POST http://localhost:4000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_id": "quantum_cck8",
    "lab_id": "starfleet",
    "project_id": "prometheus",
    "protocol_version": "2.0.0"
  }'

# 设置变量
curl -X POST http://localhost:4000/api/session/var \
  -H "Content-Type: application/json" \
  -d '{"var_id": "mission_code", "value": "PRO-2024-001"}'

# 批量设置变量
curl -X POST http://localhost:4000/api/session/vars \
  -H "Content-Type: application/json" \
  -d '{"data": {"culture_temp": 37.0, "co2_level": 5.0}}'

# 完成步骤
curl -X POST http://localhost:4000/api/session/step/open_portal/complete?annotation=已校准

# 通过检查点
curl -X POST http://localhost:4000/api/session/check/dimension_stability/pass?annotation=稳定

# 上传文件到 Session
curl -X POST http://localhost:4000/api/session/upload \
  -F "var_id=cell_initial_photo" \
  -F "file=@cell_photo.png"

# 获取当前 Session 状态
curl http://localhost:4000/api/session/current

# 保存 Session
curl -X POST http://localhost:4000/api/session/save

# 结束 Session
curl -X POST http://localhost:4000/api/session/end?save=true
```

### 加载已有 Record

```python
# Python
session = client.load_record_session("airalogy.id.record.xxx.v.1")
session.set_var("new_field", "new_value")
session.increment_version()
session.save()
```

```bash
# HTTP
curl -X POST http://localhost:4000/api/session/load/airalogy.id.record.xxx.v.1
```

## Record JSON 格式

生成的 Record 遵循 Airalogy 标准格式：

```json
{
  "airalogy_record_id": "airalogy.id.record.<uuid>.v.<version>",
  "record_id": "<uuid>",
  "record_version": 1,
  "metadata": {
    "airalogy_protocol_id": "airalogy.id.lab.<lab>.project.<project>.protocol.<protocol>.v.<version>",
    "lab_id": "...",
    "project_id": "...",
    "protocol_id": "...",
    "protocol_version": "...",
    "record_num": 1,
    "record_current_version_submission_time": "2025-12-26T10:00:00+08:00",
    "record_current_version_submission_user_id": "...",
    "record_initial_version_submission_time": "2025-12-26T09:00:00+08:00",
    "record_initial_version_submission_user_id": "...",
    "sha1": "..."
  },
  "data": {
    "var": {
      "var_id_1": "value",
      "var_id_2": 123,
      "file_field": "airalogy.id.file.<uuid>.<ext>",
      "table_field": [{"col1": "a", "col2": 1}, ...]
    },
    "step": {
      "step_id_1": {"checked": null, "annotation": ""},
      "step_id_2": {"checked": true, "annotation": "已完成"}
    },
    "check": {
      "check_id_1": {"checked": true, "annotation": "通过"},
      "check_id_2": {"checked": false, "annotation": "未通过"}
    }
  }
}
```

## 其他 API

### 文件操作

```bash
# 上传文件
curl -X POST http://localhost:4000/api/files/upload/bytes \
  -F "file=@photo.png"

# 下载文件
curl http://localhost:4000/api/files/airalogy.id.file.xxx.png/download/bytes

# 列出文件
curl http://localhost:4000/api/files
```

### Assigner 计算

```bash
# 加载 Assigner 模块
curl -X POST http://localhost:4000/api/assigner/load \
  -H "Content-Type: application/json" \
  -d '{"module_path": "complex_example/assigner.py"}'

# 执行计算
curl -X POST http://localhost:4000/api/assigner/assign \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "inhibition_results",
    "data": {"blank_qr_mean": 0.05, "control_qr_mean": 1.2, ...}
  }'
```

### 版本信息

```bash
curl http://localhost:4000/api/version
```
