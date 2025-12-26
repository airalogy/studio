"""
🌌 星际联邦生物实验协议 - Assigner 定义

配合 protocol.aimd 使用，实现自动计算逻辑。

================================================================================
Airalogy Assigner 官方规范摘要
================================================================================

1. 基本结构:
   - 使用 @assigner 装饰器定义自动计算函数
   - assigned_fields: 要赋值的字段列表
   - dependent_fields: 依赖的输入字段列表
   - mode: "auto" (依赖变化时自动执行) 或 "manual" (手动触发)

2. 返回值:
   - 必须返回 AssignerResult 对象
   - assigned_fields 字典包含计算结果

3. 重要原则:
   - assigned_fields 中的每个字段必须在 protocol.aimd 中有对应的模板位置
   - 这是 UI 渲染的依据，缺失会导致结果无处显示

4. 支持的赋值类型:
   - 普通变量: str, int, float, bool 等基本类型
   - CheckValue: 用于 {{check|id}} 模板，包含 checked (bool) 和 annotation (str)
   - list[dict]: 用于表格变量 {{var|id, subvars=[...]}}，整体替换表格数据
   - 表格子字段: 使用 "table_name.subvar_name" 格式计算表格内的单个字段

参考文档: https://github.com/airalogy/airalogy/blob/main/docs/en/syntax/assigner.md
================================================================================
"""

from airalogy.assigner import assigner, AssignerResult, DefaultAssigner
from airalogy.models import CheckValue


# ============================================================
# 示例 1: 从表格读取数据，计算并整体赋值到另一个表格
# ============================================================
#
# 【官方规范】
# - dependent_fields 可以包含表格变量名，会收到 list[dict] 格式的数据
# - assigned_fields 可以整体赋值 list[dict] 到表格变量
# - 返回的 list 中每个 dict 的 key 必须与表格的 subvars 定义一致
#
# 【对应的 protocol.aimd 模板】
# {{var|inhibition_results,
#     subvars=[
#         var(energy_level: float),
#         var(treatment_qr_mean: float),
#         var(inhibition_rate: float),
#         var(dimension_correction: float),
#         var(confidence_level: str),
#         var(notes: str)
#     ]
# }}
#
# 【对应的 model.py 定义】
# inhibition_results: list[InhibitionResult]
# ============================================================

@assigner(
    assigned_fields=["inhibition_results"],
    dependent_fields=["blank_qr_mean", "control_qr_mean", "quantum_measurements"],
    mode="auto",
)
def calculate_inhibition_rates(dep: dict) -> AssignerResult:
    """
    根据量子共振测量数据自动计算各能量等级的抑制率
    
    【Assigner 模式】auto - 当 dependent_fields 中任一字段变化时自动执行
    
    【输入】
    - blank_qr_mean: float - 空白对照的量子共振均值
    - control_qr_mean: float - 阴性对照的量子共振均值  
    - quantum_measurements: list[dict] - 量子共振测量表格数据
    
    【输出】
    - inhibition_results: list[dict] - 整体替换抑制率结果表格
    
    【计算公式】
    抑制率 (%) = [1 - (处理组QR - 空白QR) / (对照组QR - 空白QR)] × 100%
    """
    blank = dep.get("blank_qr_mean") or 0
    control = dep.get("control_qr_mean") or 1
    measurements = dep.get("quantum_measurements") or []
    
    if not measurements:
        return AssignerResult(
            success=False,
            error_message="缺少量子共振测量数据"
        )
    
    # 按能量等级分组计算
    energy_groups: dict[float, list[float]] = {}
    for m in measurements:
        if m.get("group_type") == "处理组":
            energy = m.get("energy_level", 0)
            qr = m.get("quantum_resonance", 0)
            if energy not in energy_groups:
                energy_groups[energy] = []
            energy_groups[energy].append(qr)
    
    results = []
    for energy_level, qr_values in sorted(energy_groups.items(), reverse=True):
        treatment_qr_mean = sum(qr_values) / len(qr_values) if qr_values else 0
        
        # 计算抑制率
        if control - blank != 0:
            rate = (1 - (treatment_qr_mean - blank) / (control - blank)) * 100
            rate = max(0, min(100, rate))
        else:
            rate = 0
        
        # 评估置信度
        if rate > 70:
            confidence = "高"
        elif rate > 30:
            confidence = "中"
        else:
            confidence = "低"
        
        # 返回的 dict key 必须与 subvars 定义一致
        results.append({
            "energy_level": energy_level,
            "treatment_qr_mean": round(treatment_qr_mean, 4),
            "inhibition_rate": round(rate, 2),
            "dimension_correction": 1.0,
            "confidence_level": confidence,
            "notes": ""
        })
    
    return AssignerResult(assigned_fields={"inhibition_results": results})


# ============================================================
# 示例 2: 使用 CheckValue 赋值到 check 模板
# ============================================================
#
# 【官方规范】
# - CheckValue 是 Airalogy 提供的模型，用于 checkpoint 类型的字段
# - 包含两个属性:
#   - checked: bool - 检查是否通过
#   - annotation: str - 检查结果的说明文字
# - assigned_field 必须对应 protocol.aimd 中的 {{check|id}} 模板
#
# 【对应的 protocol.aimd 模板】
# {{check|dimension_stability_check}} 维度稳定性校验
#
# 【官方示例代码】
# from airalogy.models import CheckValue
# return AssignerResult(
#     assigned_fields={
#         "check_field": CheckValue(
#             checked=True,
#             annotation="检查通过的说明"
#         )
#     }
# )
# ============================================================

@assigner(
    assigned_fields=["dimension_stability_check"],
    dependent_fields=["stability_field"],
    mode="auto",
)
def check_dimension_stability(dep: dict) -> AssignerResult:
    """
    检查维度稳定场强度是否满足实验要求 (≥95%)
    
    【Assigner 模式】auto - 当 stability_field 变化时自动执行
    
    【输入】
    - stability_field: float - 时空稳定场强度百分比
    
    【输出】
    - dimension_stability_check: CheckValue - 对应 {{check|dimension_stability_check}}
    
    【CheckValue 结构】
    class CheckValue(BaseModel):
        checked: bool      # 检查是否通过
        annotation: str    # 检查结果说明
    """
    stability = dep.get("stability_field", 0)
    is_stable = stability >= 95
    
    return AssignerResult(
        assigned_fields={
            "dimension_stability_check": CheckValue(
                checked=is_stable,
                annotation=f"稳定场强度 {stability}% {'✓ 满足安全要求' if is_stable else '✗ 低于安全阈值 95%'}"
            )
        }
    )


# ============================================================
# 示例 3: CheckValue 的另一个示例 - 温度校验
# ============================================================
#
# 【对应的 protocol.aimd 模板】
# {{check|temperature_check}} 培养温度校验
# ============================================================

@assigner(
    assigned_fields=["temperature_check"],
    dependent_fields=["culture_temp"],
    mode="auto",
)
def check_culture_temperature(dep: dict) -> AssignerResult:
    """
    检查培养温度是否在标准范围内 (36-38°C)
    
    【Assigner 模式】auto
    
    【输入】
    - culture_temp: float - 培养温度 (°C)
    
    【输出】
    - temperature_check: CheckValue - 对应 {{check|temperature_check}}
    """
    temp = dep.get("culture_temp", 0)
    is_valid = 36 <= temp <= 38
    
    return AssignerResult(
        assigned_fields={
            "temperature_check": CheckValue(
                checked=is_valid,
                annotation=f"培养温度 {temp}°C {'✓ 在标准范围内' if is_valid else '✗ 超出标准范围 36-38°C'}"
            )
        }
    )


# ============================================================
# 示例 4: 手动触发模式 (mode="manual") - 整体生成表格数据
# ============================================================
#
# 【官方规范】
# - mode="manual" 表示不会自动执行，需要用户手动触发
# - 适用于: 生成初始数据、批量填充、可能覆盖用户输入的场景
# - 与 mode="auto" 的区别:
#   - auto: dependent_fields 变化时自动执行
#   - manual: 仅在用户点击触发按钮时执行
#
# 【对应的 protocol.aimd 模板】
# {{var|energy_dilutions, subvars=[...]}}
# ============================================================

@assigner(
    assigned_fields=["energy_dilutions"],
    dependent_fields=["base_energy_level"],
    mode="manual",  # 手动触发，避免覆盖用户已编辑的数据
)
def generate_energy_dilutions(dep: dict) -> AssignerResult:
    """
    根据基础能量浓度自动生成标准梯度配制表
    
    【Assigner 模式】manual - 需要用户手动触发，不会自动执行
    
    【使用场景】
    - 生成初始模板数据
    - 用户可能已手动编辑表格，自动执行会覆盖
    
    【输入】
    - base_energy_level: float - 基础能量浓度 (TeV)
    
    【输出】
    - energy_dilutions: list[dict] - 整体替换能量梯度配制表
    """
    base = dep.get("base_energy_level", 1000)
    
    # 标准稀释梯度: 100%, 50%, 25%, 10%, 0% (对照)
    ratios = [1.0, 0.5, 0.25, 0.1, 0]
    phases = ["α", "α", "β", "β", "γ"]
    wells = ["A1", "A2", "A3", "A4", "A5"]
    
    dilutions = []
    for ratio, phase, well in zip(ratios, phases, wells):
        energy = base * ratio
        source_vol = ratio * 10
        stabilizer_vol = 100 - source_vol
        
        dilutions.append({
            "energy_level": energy,
            "source_volume": source_vol,
            "stabilizer_volume": stabilizer_vol,
            "well_position": well,
            "dimension_phase": phase,
        })
    
    return AssignerResult(assigned_fields={"energy_dilutions": dilutions})


# ============================================================
# 示例 5: 普通变量赋值 - 返回数值类型
# ============================================================
#
# 【官方规范】
# - 最简单的 Assigner 用法: 计算并返回基本类型值
# - 支持的类型: str, int, float, bool, None
# - 复杂类型 (如 datetime) 需要转换为 JSON 兼容格式 (如 ISO 字符串)
#
# 【对应的 protocol.aimd 模板】
# 预计实验总时长：{{var|estimated_total_time: float}} 小时
#
# 【最佳实践】
# - 可量化的值应使用数值类型 (int/float)，便于后续计算和数据分析
# - 单位在 aimd 模板中标注，而非拼接到值中
# ============================================================

@assigner(
    assigned_fields=["estimated_total_time"],
    dependent_fields=["adhesion_time", "treatment_duration", "cck8_incubation_time"],
    mode="manual",
)
def estimate_total_time(dep: dict) -> AssignerResult:
    """
    估算实验总时长
    
    【Assigner 模式】auto
    
    【输入】
    - adhesion_time: float - 贴壁时间 (小时)
    - treatment_duration: float - 处理时间 (小时)
    - cck8_incubation_time: float - CCK-8 孵育时间 (小时)
    
    【输出】
    - estimated_total_time: float - 总时长数值 (小时)
    
    【设计原则】
    - 返回数值类型而非格式化字符串
    - 单位 "小时" 在 protocol.aimd 模板中标注
    - 保持数据的可计算性和严谨性
    """
    adhesion = dep.get("adhesion_time", 0) or 0
    treatment = dep.get("treatment_duration", 0) or 0
    cck8 = dep.get("cck8_incubation_time", 0) or 0
    
    setup_time = 2  # 准备时间
    measurement_time = 1  # 测量时间
    
    total = adhesion + treatment + cck8 + setup_time + measurement_time
    
    # 返回数值，保留一位小数
    return AssignerResult(
        assigned_fields={
            "estimated_total_time": round(total, 1)
        }
    )


# ============================================================
# 【补充说明】表格子字段计算 (本示例未使用，但列出供参考)
# ============================================================
#
# 如果需要计算表格内某一列的值（基于同行其他列），使用点号语法:
#
# @assigner(
#     assigned_fields=["table_name.calculated_column"],
#     dependent_fields=["table_name.column_a", "table_name.column_b"],
#     mode="auto",
# )
# def calculate_table_column(dep: dict) -> AssignerResult:
#     a = dep["table_name.column_a"]
#     b = dep["table_name.column_b"]
#     result = a + b
#     return AssignerResult(
#         assigned_fields={"table_name.calculated_column": result}
#     )
#
# 【限制】
# - 只能引用同一个表格的字段
# - 不支持跨表格计算
# ============================================================


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    
    # 模拟数据
    test_data = {
        "blank_qr_mean": 0.05,
        "control_qr_mean": 1.25,
        "quantum_measurements": [
            {"well_position": "A1", "quantum_resonance": 0.35, "group_type": "处理组", "energy_level": 100.0},
            {"well_position": "A2", "quantum_resonance": 0.55, "group_type": "处理组", "energy_level": 50.0},
            {"well_position": "A3", "quantum_resonance": 0.85, "group_type": "处理组", "energy_level": 25.0},
            {"well_position": "A4", "quantum_resonance": 1.05, "group_type": "处理组", "energy_level": 10.0},
            {"well_position": "A5", "quantum_resonance": 1.20, "group_type": "对照组", "energy_level": 0.0},
            {"well_position": "A6", "quantum_resonance": 0.05, "group_type": "空白组", "energy_level": 0.0},
        ],
        "stability_field": 99.5,
        "culture_temp": 37.0,
        "base_energy_level": 1000.0,
        "adhesion_time": 24.0,
        "treatment_duration": 48.0,
        "cck8_incubation_time": 2.0,
    }
    
    print("=" * 60)
    print("🌌 星际联邦生物实验协议 - Assigner 测试")
    print("=" * 60)
    
    results = {}
    
    # 1. 抑制率计算 (表格整体赋值)
    r = DefaultAssigner.assign("inhibition_results", test_data)
    if r.success:
        results.update(r.assigned_fields)
    
    # 2. 维度稳定性检查 (CheckValue)
    r = DefaultAssigner.assign("dimension_stability_check", test_data)
    if r.success:
        results.update(r.assigned_fields)
    
    # 3. 温度检查 (CheckValue)
    r = DefaultAssigner.assign("temperature_check", test_data)
    if r.success:
        results.update(r.assigned_fields)
    
    # 4. 时间估算 (普通字符串)
    r = DefaultAssigner.assign("estimated_total_time", test_data)
    if r.success:
        results.update(r.assigned_fields)
    
    # 输出结果
    print("\n📊 抑制率计算结果 (list[dict] → 表格):")
    if "inhibition_results" in results:
        for r in results["inhibition_results"]:
            print(f"  能量 {r['energy_level']:>6.1f} TeV → 抑制率 {r['inhibition_rate']:>5.1f}% ({r['confidence_level']})")
    
    print("\n✅ 自动校验结果 (CheckValue → check 模板):")
    if "dimension_stability_check" in results:
        check = results["dimension_stability_check"]
        print(f"  维度稳定性: {'✓' if check.checked else '✗'} {check.annotation}")
    
    if "temperature_check" in results:
        check = results["temperature_check"]
        print(f"  培养温度: {'✓' if check.checked else '✗'} {check.annotation}")
    
    print("\n⏱️ 时间估算 (float → var 模板):")
    if "estimated_total_time" in results:
        print(f"  预计总时长: {results['estimated_total_time']} 小时")
    
    print("\n📋 已注册的 Assigner 字段:")
    for field, info in DefaultAssigner.all_assigned_fields().items():
        print(f"  - {field} (mode={info.get('mode', 'unknown')})")
