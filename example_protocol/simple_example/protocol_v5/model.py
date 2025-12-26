"""
🌌 星际联邦生物实验协议 - Pydantic 模型定义

本文件定义了 protocol.aimd 中所有变量的类型、默认值和验证规则。
展示了 Airalogy 所有自有类型的使用方法。

使用方式：
1. 将此文件与 protocol.aimd 放在同一目录下
2. Airalogy 会自动加载 VarModel 类来验证用户输入
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================
# Airalogy 自有类型导入
# ============================================================

try:
    from airalogy.types import (
        # 自动填充类型
        UserName,           # 自动填充当前用户名
        CurrentTime,        # 自动填充当前时间
        CurrentRecordId,    # 自动填充当前记录 ID
        VersionStr,         # 语义化版本号
        
        # 文件上传类型
        FileIdPNG,          # PNG 图片
        FileIdJPG,          # JPG 图片
        FileIdTIFF,         # TIFF 图片
        FileIdPDF,          # PDF 文档
        FileIdCSV,          # CSV 数据文件
        FileIdMP4,          # MP4 视频
        
        # 关联引用类型
        RecordId,           # 关联其他记录
        
        # 特殊输入类型
        AiralogyMarkdown,   # Markdown 编辑器
        PyStr,              # Python 代码编辑器
        IgnoreStr,          # 敏感数据（不持久化）
    )
except ImportError:
    # 本地测试时的模拟类型
    UserName = str
    CurrentTime = datetime
    CurrentRecordId = str
    VersionStr = str
    FileIdPNG = str
    FileIdJPG = str
    FileIdTIFF = str
    FileIdPDF = str
    FileIdCSV = str
    FileIdMP4 = str
    RecordId = str
    AiralogyMarkdown = str
    PyStr = str
    IgnoreStr = str


# ============================================================
# 变量表格子模型
# ============================================================

class ResearchTeamMember(BaseModel):
    """研究团队成员 - 跨维度实验参与人员"""
    
    name: str = Field(default="", title="研究员姓名", description="星际联邦注册名")
    species: str = Field(default="人类", title="种族", description="生物种族分类")
    home_dimension: str = Field(default="D-616", title="原生维度", description="研究员来自的平行宇宙")
    clearance_level: int = Field(default=1, title="安全等级", ge=1, le=10, description="星际联邦安全许可等级")
    specialty: str = Field(default="", title="专业领域", description="研究专长")


class EnergyDilution(BaseModel):
    """时空能量梯度配制记录"""
    
    energy_level: float = Field(default=0.0, title="能量等级 (TeV)", ge=0)
    source_volume: float = Field(default=0.0, title="源能量用量 (μL)", ge=0)
    stabilizer_volume: float = Field(default=100.0, title="稳定剂用量 (μL)", ge=0)
    well_position: str = Field(default="", title="孔位")
    dimension_phase: Literal["α", "β", "γ"] = Field(default="α", title="维度相位")


class QuantumMeasurement(BaseModel):
    """量子共振测量记录"""
    
    well_position: str = Field(default="", title="孔位")
    od_value: float = Field(default=0.0, title="OD值 (450nm)", ge=0, le=4.0)
    quantum_resonance: float = Field(default=0.0, title="量子共振值 (QR)", ge=0)
    dimension_interference: float = Field(default=0.0, title="维度干扰系数", ge=0, le=1.0)
    group_type: Literal["对照组", "处理组", "空白组"] = Field(default="处理组", title="分组")
    energy_level: float = Field(default=0.0, title="能量等级 (TeV)", ge=0)


class InhibitionResult(BaseModel):
    """时空抑制率计算结果"""
    
    energy_level: float = Field(default=0.0, title="能量等级 (TeV)", ge=0)
    treatment_qr_mean: float = Field(default=0.0, title="处理组QR均值", ge=0)
    inhibition_rate: float = Field(default=0.0, title="抑制率 (%)", ge=0, le=100)
    dimension_correction: float = Field(default=1.0, title="维度校正系数", ge=0.5, le=2.0)
    confidence_level: Literal["高", "中", "低"] = Field(default="高", title="置信度")
    notes: str = Field(default="", title="备注", max_length=500)


# ============================================================
# 默认数据工厂函数
# ============================================================

def default_research_team() -> list[ResearchTeamMember]:
    """预填充的研究团队模板"""
    return [
        ResearchTeamMember(
            name="艾丽卡·陈",
            species="人类",
            home_dimension="D-616",
            clearance_level=7,
            specialty="跨维度细胞生物学"
        ),
        ResearchTeamMember(
            name="泽克斯-7",
            species="仿生人",
            home_dimension="D-199",
            clearance_level=5,
            specialty="量子共振分析"
        ),
    ]


def default_energy_dilutions() -> list[EnergyDilution]:
    """预填充的能量梯度模板"""
    return [
        EnergyDilution(energy_level=100.0, source_volume=10.0, stabilizer_volume=90.0, well_position="A1", dimension_phase="α"),
        EnergyDilution(energy_level=50.0, source_volume=5.0, stabilizer_volume=95.0, well_position="A2", dimension_phase="α"),
        EnergyDilution(energy_level=25.0, source_volume=2.5, stabilizer_volume=97.5, well_position="A3", dimension_phase="β"),
        EnergyDilution(energy_level=10.0, source_volume=1.0, stabilizer_volume=99.0, well_position="A4", dimension_phase="β"),
        EnergyDilution(energy_level=0.0, source_volume=0.0, stabilizer_volume=100.0, well_position="A5", dimension_phase="γ"),
    ]


def default_quantum_measurements() -> list[QuantumMeasurement]:
    """预填充的量子测量模板"""
    return [
        QuantumMeasurement(well_position="A1", group_type="处理组", energy_level=100.0),
        QuantumMeasurement(well_position="A2", group_type="处理组", energy_level=50.0),
        QuantumMeasurement(well_position="A3", group_type="处理组", energy_level=25.0),
        QuantumMeasurement(well_position="A4", group_type="处理组", energy_level=10.0),
        QuantumMeasurement(well_position="A5", group_type="对照组", energy_level=0.0),
        QuantumMeasurement(well_position="A6", group_type="空白组", energy_level=0.0),
    ]


def default_inhibition_results() -> list[InhibitionResult]:
    """预填充的抑制率结果模板"""
    return [
        InhibitionResult(energy_level=100.0, confidence_level="高", notes="高能量区"),
        InhibitionResult(energy_level=50.0, confidence_level="高"),
        InhibitionResult(energy_level=25.0, confidence_level="中"),
        InhibitionResult(energy_level=10.0, confidence_level="中", notes="低能量区"),
    ]


# ============================================================
# 主模型定义
# ============================================================

class VarModel(BaseModel):
    """
    🌌 星际联邦生物实验协议 - 变量模型
    
    展示了 Airalogy 所有自有类型的使用方法
    """
    
    # ========================================================
    # 自动填充类型示例
    # ========================================================
    # 这些字段会自动获取值，无需用户手动输入
    
    operator: UserName = Field(
        title="星际研究员",
        description="自动填充当前登录用户的星际身份 (UserName 类型)"
    )
    
    record_time: CurrentTime = Field(
        title="时空坐标记录",
        description="自动填充当前时间 (CurrentTime 类型)"
    )
    
    current_record_id: CurrentRecordId = Field(
        title="量子签名 ID",
        description="自动填充当前记录的唯一标识 (CurrentRecordId 类型)"
    )
    
    protocol_version: VersionStr = Field(
        default="2.0.0",
        title="协议版本",
        description="语义化版本号 (VersionStr 类型，格式 x.y.z)"
    )
    
    # ========================================================
    # 基本信息
    # ========================================================
    
    mission_code: str = Field(
        default="PRO-2024-001",
        title="任务代号",
        description="星际联邦任务编码",
        pattern=r"^[A-Z]{3}-\d{4}-\d{3}$"
    )
    
    dimension_id: str = Field(
        default="D-616",
        title="维度编号",
        description="当前实验所在的平行宇宙维度",
        pattern=r"^D-\d{1,4}$"
    )
    
    research_station: str = Field(
        default="",
        title="研究站点",
        description="星际研究站编号"
    )
    
    # ========================================================
    # 研究团队表格 (变量表格示例)
    # ========================================================
    
    research_team: list[ResearchTeamMember] = Field(
        default_factory=default_research_team,
        title="研究团队成员表",
        description="跨维度实验参与人员登记"
    )
    
    # ========================================================
    # 关联记录类型示例 (RecordId)
    # ========================================================
    # UI 会渲染为下拉选择框，可选择其他实验记录
    
    previous_experiment: Optional[RecordId] = Field(
        default=None,
        title="关联的前序实验",
        description="选择关联的前序实验记录 (RecordId 类型)"
    )
    
    # ========================================================
    # 样本与培养参数
    # ========================================================
    
    sample_source_dimension: str = Field(
        default="D-199",
        title="样本维度",
        description="细胞样本采集的平行宇宙编号"
    )
    
    cell_line_name: str = Field(
        default="Hela-X7",
        title="细胞系名称",
        description="跨维度肿瘤细胞系编号"
    )
    
    seeding_density: int = Field(
        default=5000,
        title="接种密度",
        ge=1000,
        le=50000
    )
    
    culture_temp: float = Field(
        default=37.0,
        title="培养温度 (°C)",
        ge=20,
        le=45
    )
    
    co2_level: float = Field(
        default=5.0,
        title="CO₂浓度 (%)",
        ge=0,
        le=10
    )
    
    stability_field: float = Field(
        default=99.9,
        title="稳定场强度 (%)",
        ge=95,
        le=100
    )
    
    adhesion_time: float = Field(
        default=24.0,
        title="贴壁时间 (小时)",
        ge=0
    )
    
    # ========================================================
    # 文件上传类型示例 (FileId*)
    # ========================================================
    # 这些字段会渲染为文件上传按钮
    
    incubator_settings_photo: Optional[FileIdPNG] = Field(
        default=None,
        title="培养箱设置截图",
        description="上传培养箱参数设置截图 (FileIdPNG 类型)"
    )
    
    cell_initial_photo: Optional[FileIdPNG] = Field(
        default=None,
        title="细胞初始状态照片",
        description="上传细胞初始形态照片 (FileIdPNG 类型)"
    )
    
    cell_before_photo: Optional[FileIdPNG] = Field(
        default=None,
        title="细胞处理前照片",
        description="能量处理前的细胞形态 (FileIdPNG 类型)"
    )
    
    cell_after_photo: Optional[FileIdJPG] = Field(
        default=None,
        title="细胞处理后照片",
        description="能量处理后的细胞形态 (FileIdJPG 类型)"
    )
    
    dimension_rift_hologram: Optional[FileIdTIFF] = Field(
        default=None,
        title="维度裂隙全息图",
        description="高精度维度裂隙成像 (FileIdTIFF 类型)"
    )
    
    raw_data_file: Optional[FileIdCSV] = Field(
        default=None,
        title="原始数据文件",
        description="量子光谱仪导出的原始数据 (FileIdCSV 类型)"
    )
    
    experiment_video: Optional[FileIdMP4] = Field(
        default=None,
        title="实验过程视频",
        description="实验全程录像 (FileIdMP4 类型)"
    )
    
    final_report: Optional[FileIdPDF] = Field(
        default=None,
        title="实验报告",
        description="最终实验报告文档 (FileIdPDF 类型)"
    )
    
    # ========================================================
    # 时空能量处理参数
    # ========================================================
    
    energy_source: str = Field(
        default="黑洞边界辐射",
        title="能量来源",
        description="时空裂隙能量的采集来源"
    )
    
    base_energy_level: float = Field(
        default=1000.0,
        title="基础能量 (TeV)",
        ge=0
    )
    
    treatment_duration: float = Field(
        default=48.0,
        title="处理时间 (小时)",
        ge=1,
        le=168
    )
    
    # ========================================================
    # 能量梯度配制表格
    # ========================================================
    
    energy_dilutions: list[EnergyDilution] = Field(
        default_factory=default_energy_dilutions,
        title="时空能量梯度配制表",
        description="各能量梯度的配制记录"
    )
    
    # ========================================================
    # 量子检测参数
    # ========================================================
    
    cck8_incubation_time: float = Field(
        default=2.0,
        title="CCK-8孵育时间 (小时)",
        ge=0.5,
        le=4
    )
    
    # ========================================================
    # 量子测量表格
    # ========================================================
    
    quantum_measurements: list[QuantumMeasurement] = Field(
        default_factory=default_quantum_measurements,
        title="量子共振测量记录表",
        description="各孔的量子共振数据"
    )
    
    # ========================================================
    # 数据分析参数
    # ========================================================
    
    blank_qr_mean: Optional[float] = Field(
        default=None,
        title="空白QR均值",
        ge=0
    )
    
    control_qr_mean: Optional[float] = Field(
        default=None,
        title="对照组QR均值",
        ge=0
    )
    
    # ========================================================
    # 代码编辑器类型示例 (PyStr)
    # ========================================================
    
    data_processing_script: Optional[PyStr] = Field(
        default="""# 量子共振数据处理脚本
import numpy as np

def calculate_inhibition_rate(treatment_qr, control_qr, blank_qr, dimension_correction=1.0):
    \"\"\"计算时空抑制率\"\"\"
    if control_qr - blank_qr == 0:
        return 0.0
    rate = (1 - (treatment_qr - blank_qr) / (control_qr - blank_qr)) * dimension_correction * 100
    return max(0, min(100, rate))

# 示例计算
result = calculate_inhibition_rate(0.5, 1.2, 0.05, 1.0)
print(f"抑制率: {result:.2f}%")
""",
        title="数据处理脚本",
        description="Python 数据处理代码 (PyStr 类型，带语法高亮)"
    )
    
    # ========================================================
    # 抑制率结果表格
    # ========================================================
    
    inhibition_results: list[InhibitionResult] = Field(
        default_factory=default_inhibition_results,
        title="时空抑制率计算结果表",
        description="各能量等级下的抑制率"
    )
    
    # ========================================================
    # Markdown 编辑器类型示例 (AiralogyMarkdown)
    # ========================================================
    
    experiment_notes: Optional[AiralogyMarkdown] = Field(
        default="""## 实验观察记录

### 异常现象
- 在能量等级 100 TeV 时观察到轻微的维度闪烁
- A3 孔位出现短暂的时空涟漪

### 结论
本次实验成功验证了时空裂隙能量对跨维度肿瘤细胞的抑制作用。

### 后续建议
1. 增加更多能量梯度点
2. 延长观察时间至 72 小时
3. 尝试不同维度相位组合
""",
        title="实验备注",
        description="Markdown 格式的实验备注 (AiralogyMarkdown 类型)"
    )
    
    # ========================================================
    # 敏感数据类型示例 (IgnoreStr)
    # ========================================================
    # 运行时可用，但保存时会被清空
    
    federation_api_key: Optional[IgnoreStr] = Field(
        default=None,
        title="星际联邦 API 密钥",
        description="用于上传结果到联邦数据库，保存时会自动清空 (IgnoreStr 类型)"
    )


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    # 创建示例数据
    sample_data = VarModel(
        operator="airalogy.id.user.alice-chen-d616",
        record_time=datetime.now(),
        current_record_id="airalogy.id.record.quantum-exp-001",
        mission_code="PRO-2024-001",
        dimension_id="D-616",
        research_station="Prometheus-7",
        cell_line_name="Hela-X7",
        energy_source="黑洞边界辐射",
        base_energy_level=1000.0,
        blank_qr_mean=0.05,
        control_qr_mean=1.25,
    )
    
    print("=== 🌌 星际联邦生物实验协议 - 示例数据 ===\n")
    print(sample_data.model_dump_json(indent=2, ensure_ascii=False))


# ============================================================
# Airalogy 自有类型速查表
# ============================================================
"""
┌─────────────────────────────────────────────────────────────┐
│                    Airalogy 自有类型速查表                    │
├─────────────────────────────────────────────────────────────┤
│ 类型              │ 用途                │ UI 表现            │
├───────────────────┼─────────────────────┼────────────────────┤
│ UserName          │ 当前用户名          │ 自动填充           │
│ CurrentTime       │ 当前时间            │ 自动填充           │
│ CurrentRecordId   │ 当前记录 ID         │ 自动填充           │
│ CurrentProtocolId │ 当前协议 ID         │ 自动填充           │
│ VersionStr        │ 语义化版本号        │ 文本框 + 验证      │
├───────────────────┼─────────────────────┼────────────────────┤
│ FileIdPNG         │ PNG 图片上传        │ 上传按钮           │
│ FileIdJPG         │ JPG 图片上传        │ 上传按钮           │
│ FileIdTIFF        │ TIFF 图片上传       │ 上传按钮           │
│ FileIdPDF         │ PDF 文档上传        │ 上传按钮           │
│ FileIdCSV         │ CSV 数据上传        │ 上传按钮           │
│ FileIdMP4         │ MP4 视频上传        │ 上传按钮           │
├───────────────────┼─────────────────────┼────────────────────┤
│ RecordId          │ 关联其他记录        │ 下拉选择框         │
│ ProtocolId        │ 协议 ID 验证        │ 文本框 + 验证      │
├───────────────────┼─────────────────────┼────────────────────┤
│ AiralogyMarkdown  │ Markdown 内容       │ Markdown 编辑器    │
│ PyStr             │ Python 代码         │ 代码编辑器         │
│ JsStr             │ JavaScript 代码     │ 代码编辑器         │
│ TsStr             │ TypeScript 代码     │ 代码编辑器         │
│ IgnoreStr         │ 敏感数据            │ 文本框(不持久化)   │
│ Recommended[T]    │ 推荐默认值          │ 预填充可修改       │
└─────────────────────────────────────────────────────────────┘

注意事项：
1. 自有类型必须在 model.py 中定义，不能在 AIMD 内联使用
2. 自动填充类型无需用户输入，系统自动获取
3. 文件类型存储的是 ID，格式：airalogy.id.file.<uuid>.<ext>
4. IgnoreStr 运行时可用，保存时清空，适合 API Key
5. Optional 字段使用 Optional[Type] 或 Type | None
"""
