# 🌌 星际联邦实验协议 - 演示素材

本文件夹包含 `protocol.aimd` 跨维度科幻实验协议的演示素材文件。

## 📁 文件清单

| 文件名 | 类型 | 对应变量 | 说明 |
|--------|------|----------|------|
| `cell_initial_photo.png` | FileIdPNG | `cell_initial_photo` | 细胞初始状态照片 |
| `incubator_settings.png` | FileIdPNG | `incubator_settings_photo` | 培养箱设置截图 |
| `cell_before_treatment.png` | FileIdPNG | `cell_before_photo` | 能量处理前细胞照片 |
| `cell_after_treatment.jpg` | FileIdJPG | `cell_after_photo` | 能量处理后细胞照片 |
| `dimension_rift_hologram.tiff` | FileIdTIFF | `dimension_rift_hologram` | 维度裂隙全息图 |
| `quantum_spectrometer_raw_data.csv` | FileIdCSV | `raw_data_file` | 量子光谱仪原始数据 |
| `experiment_video_placeholder.mp4` | FileIdMP4 | `experiment_video` | 实验过程视频（占位符） |
| `final_experiment_report.pdf` | FileIdPDF | `final_report` | 最终实验报告 |

## 🚀 快速开始

### 生成素材文件

```bash
# 基础版本（无需额外依赖）
python demo_assets/generate_demo_files.py

# 完整版本（推荐）
pip install Pillow reportlab
python demo_assets/generate_demo_files.py
```

### 依赖说明

| 依赖 | 用途 | 必需 |
|------|------|------|
| `Pillow` | 生成高质量图片 (PNG/JPG/TIFF) | 推荐 |
| `reportlab` | 生成完整 PDF 报告 | 推荐 |

没有这些依赖时，脚本会生成简化版的占位文件。

## 🎯 使用场景

1. **调试 Airalogy 文件上传功能**
   - 测试各种文件类型的上传和预览
   - 验证文件 ID 格式 `airalogy.id.file.<uuid>.<ext>`

2. **演示协议模板**
   - 向用户展示完整的实验流程
   - 演示各种 Airalogy 自有类型的使用

3. **开发测试**
   - 测试文件处理逻辑
   - 验证数据导入导出功能

## 📊 CSV 数据格式

`quantum_spectrometer_raw_data.csv` 包含模拟的 96 孔板量子共振数据：

```csv
Well_Position,Energy_Level_TeV,OD_450nm,Quantum_Resonance_QR,Dimension_Interference,Group_Type,Dimension_Phase,Timestamp
A1,100.0,0.2345,0.1892,0.0234,处理组,α,2024-01-15T10:23:45
...
```

### 数据布局

- 列 1-2: 高能量组 (100 TeV)
- 列 3-4: 中高能量组 (50 TeV)
- 列 5-6: 中能量组 (25 TeV)
- 列 7-8: 低能量组 (10 TeV)
- 列 9-10: 对照组 (0 TeV)
- 列 11-12: 空白组

## 🎨 图片风格

所有图片采用科幻风格设计：
- 深空背景色 (#0F1423)
- 青色/紫色高亮
- 网格叠加效果
- 科幻边框装饰
- 中文标注

## ⚠️ 注意事项

1. `experiment_video_placeholder.mp4` 是占位文件，不是真实视频
2. 生成的文件仅供演示，不包含真实实验数据
3. 每次运行脚本会覆盖已有文件

## 🔗 相关文件

- `../protocol.aimd` - 实验协议模板
- `../model.py` - Pydantic 模型定义
