"""
Airalogy Mock Server - HTTP API 服务

为 AIMD Studio VS Code Extension 提供本地 API 服务。
使用真实的 airalogy SDK，仅模拟 HTTP 层和本地文件存储。

启动方式:
    python -m airalogy_mock.server
    
或:
    uvicorn airalogy_mock.server:app --reload --port 4000
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, Any
import json
import base64
import importlib.util
import subprocess
import sys
from pathlib import Path

# 使用真实的 airalogy SDK
import airalogy
from airalogy.assigner import DefaultAssigner

# 本地文件/记录存储
from .client import Airalogy


app = FastAPI(
    title="Airalogy Mock Server",
    description="本地模拟 Airalogy Platform API，用于 AIMD Studio 开发测试",
    version="0.1.0-mock",
)

# CORS 配置 - 允许 VS Code Webview 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局客户端实例
client = Airalogy()


# ============================================================
# 请求/响应模型
# ============================================================

class AssignRequest(BaseModel):
    """Assigner 计算请求"""
    field_name: str
    data: dict[str, Any]


class AssignAllRequest(BaseModel):
    """批量 Assigner 计算请求"""
    data: dict[str, Any]
    mode: Optional[str] = "auto"


class RecordCreateRequest(BaseModel):
    """创建记录请求"""
    data: dict[str, Any]
    record_id: Optional[str] = None


class RecordUpdateRequest(BaseModel):
    """更新记录请求"""
    data: dict[str, Any]


class StartRecordSessionRequest(BaseModel):
    """启动 Record Session 请求"""
    protocol_id: str
    lab_id: str = "mock-lab"
    project_id: str = "mock-project"
    protocol_version: str = "1.0.0"


class SetVarRequest(BaseModel):
    """设置变量请求"""
    var_id: str
    value: Any


class SetVarsRequest(BaseModel):
    """批量设置变量请求"""
    data: dict[str, Any]


class SetStepRequest(BaseModel):
    """设置步骤请求"""
    step_id: str
    checked: Optional[bool] = None
    annotation: str = ""


class SetCheckRequest(BaseModel):
    """设置检查点请求"""
    check_id: str
    checked: bool
    annotation: str = ""


class LoadAssignerRequest(BaseModel):
    """加载 Assigner 模块请求"""
    module_path: str  # 相对于工作目录的路径


# ============================================================
# 版本信息辅助函数
# ============================================================

def _get_airalogy_version_info() -> dict:
    """获取 airalogy SDK 的详细版本信息"""
    info = {
        "version": getattr(airalogy, "__version__", "unknown"),
        "install_source": "unknown",
        "commit_id": None,
        "install_path": None,
    }
    
    # 获取安装路径
    try:
        info["install_path"] = str(Path(airalogy.__file__).parent)
    except Exception:
        pass
    
    # 尝试从 importlib.metadata 获取详细信息
    try:
        import importlib.metadata
        dist = importlib.metadata.distribution("airalogy")
        
        # 检查 direct_url.json (pip install git+https://... 会生成)
        try:
            direct_url_text = dist.read_text("direct_url.json")
            if direct_url_text:
                direct_url = json.loads(direct_url_text)
                info["direct_url"] = direct_url
                
                if "vcs_info" in direct_url:
                    info["install_source"] = "github"
                    info["commit_id"] = direct_url["vcs_info"].get("commit_id")
                    info["vcs_url"] = direct_url.get("url")
                elif direct_url.get("url", "").startswith("file://"):
                    info["install_source"] = "local"
        except (FileNotFoundError, TypeError):
            pass
            
    except Exception:
        pass
    
    # 检查是否是 editable install (开发模式)
    try:
        install_path = Path(airalogy.__file__).parent
        
        # 查找 .git 目录 (可能在 parent 或 parent.parent)
        for git_parent in [install_path.parent, install_path.parent.parent, install_path]:
            git_dir = git_parent / ".git"
            if git_dir.exists():
                info["install_source"] = "github_editable"
                info["git_root"] = str(git_parent)
                
                # 获取 commit ID
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=git_parent,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["commit_id"] = result.stdout.strip()
                except Exception:
                    pass
                
                # 获取 commit 短 ID
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--short", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=git_parent,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["commit_short"] = result.stdout.strip()
                except Exception:
                    pass
                
                # 获取分支名
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=git_parent,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["branch"] = result.stdout.strip()
                except Exception:
                    pass
                
                # 检查是否有未提交的更改
                try:
                    result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        cwd=git_parent,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["dirty"] = len(result.stdout.strip()) > 0
                except Exception:
                    pass
                
                # 获取远程 URL
                try:
                    result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        capture_output=True,
                        text=True,
                        cwd=git_parent,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["remote_url"] = result.stdout.strip()
                except Exception:
                    pass
                
                break
    except Exception:
        pass
    
    # 如果还是 unknown，默认为 pypi
    if info["install_source"] == "unknown":
        info["install_source"] = "pypi"
    
    return info


# ============================================================
# 健康检查
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "Airalogy Mock Server",
        "version": "0.1.0-mock",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/version")
async def get_version():
    """获取 airalogy SDK 和 Mock Server 的版本信息"""
    return {
        "mock_server": {
            "version": "0.1.0",
        },
        "airalogy_sdk": _get_airalogy_version_info(),
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        }
    }


# ============================================================
# Assigner API
# ============================================================

@app.post("/api/assigner/assign")
async def assign_field(req: AssignRequest):
    """执行单个字段的 Assigner 计算"""
    result = DefaultAssigner.assign(req.field_name, req.data)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)
    
    return {
        "success": True,
        "assigned_fields": _serialize_assigned_fields(result.assigned_fields),
    }


@app.post("/api/assigner/assign-all")
async def assign_all_fields(req: AssignAllRequest):
    """执行所有已注册的 Assigner 计算"""
    all_fields = DefaultAssigner.all_assigned_fields()
    result_data = dict(req.data)
    
    for field_name, info in all_fields.items():
        # 如果指定了 mode，则过滤
        if req.mode and info.get("mode") != req.mode:
            continue
        
        try:
            result = DefaultAssigner.assign(field_name, result_data)
            if result.success:
                result_data.update(_serialize_assigned_fields(result.assigned_fields))
        except Exception:
            pass  # 跳过失败的计算
    
    return {
        "success": True,
        "data": result_data,
    }


@app.get("/api/assigner/fields")
async def list_assigned_fields():
    """列出所有已注册的 Assigner 字段"""
    return DefaultAssigner.all_assigned_fields()


@app.get("/api/assigner/dependencies/{field_name}")
async def get_field_dependencies(field_name: str):
    """获取指定字段的依赖关系"""
    deps = DefaultAssigner.get_dependent_fields_of_assigned_key(field_name)
    return {"field": field_name, "dependencies": deps}


@app.post("/api/assigner/load")
async def load_assigner_module(req: LoadAssignerRequest):
    """
    动态加载 Assigner 模块
    
    用于加载 .aimd 文件同目录下的 assigner.py
    """
    module_path = Path(req.module_path)
    
    if not module_path.exists():
        raise HTTPException(status_code=404, detail=f"Module not found: {req.module_path}")
    
    try:
        spec = importlib.util.spec_from_file_location("assigner_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 返回新注册的字段
        return {
            "success": True,
            "loaded_from": str(module_path),
            "registered_fields": list(DefaultAssigner.all_assigned_fields().keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load module: {str(e)}")


# ============================================================
# 文件 API
# ============================================================

@app.post("/api/files/upload/bytes")
async def upload_file_bytes(
    file: UploadFile = File(...),
):
    """上传文件 (multipart/form-data)"""
    content = await file.read()
    result = client.upload_file_bytes(file.filename, content)
    return result


@app.post("/api/files/upload/base64")
async def upload_file_base64(
    file_name: str = Form(...),
    file_base64: str = Form(...),
):
    """上传文件 (base64)"""
    result = client.upload_file_base64(file_name, file_base64)
    return result


@app.get("/api/files/{file_id}/download/bytes")
async def download_file_bytes(file_id: str):
    """下载文件 (bytes)"""
    try:
        content = client.download_file_bytes(file_id)
        # 根据扩展名设置 Content-Type
        ext = file_id.split(".")[-1]
        media_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "pdf": "application/pdf",
            "csv": "text/csv",
            "json": "application/json",
            "mp4": "video/mp4",
        }
        media_type = media_types.get(ext, "application/octet-stream")
        return Response(content=content, media_type=media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/files/{file_id}/download/base64")
async def download_file_base64(file_id: str):
    """下载文件 (base64)"""
    try:
        content = client.download_file_base64(file_id)
        return {"file_base64": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/files/{file_id}/url")
async def get_file_url(file_id: str):
    """获取文件临时 URL"""
    try:
        url = client.get_file_url(file_id)
        return {"url": url}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """删除文件"""
    deleted = client.delete_file(file_id)
    return {"deleted": deleted}


@app.get("/api/files")
async def list_files():
    """列出所有文件"""
    return client.list_files()


# ============================================================
# 记录 API
# ============================================================

@app.post("/api/records")
async def create_record(req: RecordCreateRequest):
    """创建记录"""
    result = client.create_record(req.data, req.record_id)
    return result


@app.put("/api/records/{record_id}")
async def update_record(record_id: str, req: RecordUpdateRequest):
    """更新记录"""
    try:
        result = client.update_record(record_id, req.data)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Record not found")


@app.get("/api/records/{record_id}")
async def get_record(record_id: str):
    """获取单条记录"""
    try:
        return client.get_record(record_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Record not found")


@app.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    """删除记录"""
    deleted = client.delete_record(record_id)
    return {"deleted": deleted}


@app.get("/api/records")
async def list_records():
    """列出所有记录"""
    return client.list_records()


@app.post("/api/records/download")
async def download_records(record_ids: list[str]):
    """批量下载记录"""
    json_str = client.download_records_json(record_ids)
    return JSONResponse(content=json.loads(json_str))


# ============================================================
# Record Session API (Record 模式)
# ============================================================

@app.post("/api/session/start")
async def start_record_session(req: StartRecordSessionRequest):
    """
    启动 Record 模式
    
    创建一个新的 Record Session，用于记录实验数据
    """
    session = client.start_record_session(
        protocol_id=req.protocol_id,
        lab_id=req.lab_id,
        project_id=req.project_id,
        protocol_version=req.protocol_version,
    )
    return {
        "success": True,
        "record_id": session.airalogy_record_id,
        "protocol_id": session.airalogy_protocol_id,
    }


@app.post("/api/session/load/{record_id:path}")
async def load_record_session(record_id: str):
    """加载已有的 Record Session"""
    try:
        session = client.load_record_session(record_id)
        return {
            "success": True,
            "record_id": session.airalogy_record_id,
            "protocol_id": session.airalogy_protocol_id,
            "data": session.to_record(),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Record not found")


@app.get("/api/session/current")
async def get_current_session():
    """获取当前活跃的 Record Session"""
    session = client.get_active_session()
    if session is None:
        return {"active": False}
    
    return {
        "active": True,
        "record_id": session.airalogy_record_id,
        "protocol_id": session.airalogy_protocol_id,
        "data": session.to_record(),
    }


@app.post("/api/session/end")
async def end_record_session(save: bool = True):
    """结束 Record 模式"""
    record_id = client.end_record_session(save=save)
    return {
        "success": True,
        "saved": save,
        "record_id": record_id,
    }


@app.post("/api/session/save")
async def save_current_session():
    """保存当前 Session（不结束）"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    record_id = session.save()
    return {
        "success": True,
        "record_id": record_id,
    }


# ========================================================
# Session 变量操作
# ========================================================

@app.post("/api/session/var")
async def set_session_var(req: SetVarRequest):
    """设置单个变量"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.set_var(req.var_id, req.value)
    return {"success": True, "var_id": req.var_id}


@app.post("/api/session/vars")
async def set_session_vars(req: SetVarsRequest):
    """批量设置变量"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.set_vars(req.data)
    return {"success": True, "count": len(req.data)}


@app.get("/api/session/var/{var_id}")
async def get_session_var(var_id: str):
    """获取变量值"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    value = session.get_var(var_id)
    return {"var_id": var_id, "value": value}


@app.get("/api/session/vars")
async def get_all_session_vars():
    """获取所有变量"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    return session.get_all_vars()


# ========================================================
# Session 步骤操作
# ========================================================

@app.post("/api/session/step")
async def set_session_step(req: SetStepRequest):
    """设置步骤状态"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.set_step(req.step_id, checked=req.checked, annotation=req.annotation)
    return {"success": True, "step_id": req.step_id}


@app.post("/api/session/step/{step_id}/complete")
async def complete_session_step(step_id: str, annotation: str = ""):
    """标记步骤完成"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.complete_step(step_id, annotation=annotation)
    return {"success": True, "step_id": step_id}


@app.get("/api/session/step/{step_id}")
async def get_session_step(step_id: str):
    """获取步骤状态"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    step = session.get_step(step_id)
    return {"step_id": step_id, "data": step}


@app.get("/api/session/steps")
async def get_all_session_steps():
    """获取所有步骤"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    return session.get_all_steps()


# ========================================================
# Session 检查点操作
# ========================================================

@app.post("/api/session/check")
async def set_session_check(req: SetCheckRequest):
    """设置检查点状态"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.set_check(req.check_id, checked=req.checked, annotation=req.annotation)
    return {"success": True, "check_id": req.check_id}


@app.post("/api/session/check/{check_id}/pass")
async def pass_session_check(check_id: str, annotation: str = ""):
    """通过检查点"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.pass_check(check_id, annotation=annotation)
    return {"success": True, "check_id": check_id, "checked": True}


@app.post("/api/session/check/{check_id}/fail")
async def fail_session_check(check_id: str, annotation: str = ""):
    """未通过检查点"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    session.fail_check(check_id, annotation=annotation)
    return {"success": True, "check_id": check_id, "checked": False}


@app.get("/api/session/check/{check_id}")
async def get_session_check(check_id: str):
    """获取检查点状态"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    check = session.get_check(check_id)
    return {"check_id": check_id, "data": check}


@app.get("/api/session/checks")
async def get_all_session_checks():
    """获取所有检查点"""
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    return session.get_all_checks()


# ========================================================
# Session 文件上传（自动关联到当前 Session）
# ========================================================

@app.post("/api/session/upload")
async def upload_file_to_session(
    var_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    上传文件并自动关联到当前 Session 的变量
    
    文件会被上传，file_id 会自动设置到指定的 var_id
    """
    session = client.get_active_session()
    if session is None:
        raise HTTPException(status_code=400, detail="No active session")
    
    content = await file.read()
    result = client.upload_file_bytes(file.filename, content)
    
    # 自动设置到 session 变量
    session.set_var(var_id, result["id"])
    
    return {
        "success": True,
        "var_id": var_id,
        "file_id": result["id"],
        "file_name": result["file_name"],
    }


# ============================================================
# 上下文 API
# ============================================================

@app.get("/api/context/user")
async def get_current_user():
    """获取当前用户"""
    return {"user": client.get_current_user()}


@app.get("/api/context/time")
async def get_current_time():
    """获取当前时间"""
    return {"time": client.get_current_time()}


@app.get("/api/context/protocol")
async def get_protocol_id():
    """获取当前协议 ID"""
    return {"protocol_id": client.get_protocol_id()}


# ============================================================
# 导出 API
# ============================================================

class ExportRequest(BaseModel):
    """导出请求"""
    data: dict[str, Any]
    format: str = "json"  # json, csv, excel, pdf, html
    config: Optional[dict] = None
    table_field: Optional[str] = None  # CSV 导出时指定表格字段


@app.post("/api/export")
async def export_data(req: ExportRequest):
    """导出数据为指定格式"""
    try:
        from aimd_studio.export import export_json, export_csv, export_excel, export_pdf, export_html
        from aimd_studio.export.base import ExportConfig
        
        config = ExportConfig(**req.config) if req.config else ExportConfig()
        
        exporters = {
            "json": lambda: export_json(req.data, config=config),
            "csv": lambda: export_csv(req.data, table_field=req.table_field, config=config),
            "excel": lambda: export_excel(req.data, config=config),
            "pdf": lambda: export_pdf(req.data, config=config),
            "html": lambda: export_html(req.data, config=config),
        }
        
        if req.format not in exporters:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {req.format}")
        
        result = exporters[req.format]()
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        if result.output_bytes:
            # 返回文件内容
            content_types = {
                "json": "application/json",
                "csv": "text/csv",
                "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf",
                "html": "text/html",
            }
            return Response(
                content=result.output_bytes,
                media_type=content_types.get(req.format, "application/octet-stream"),
                headers={
                    "Content-Disposition": f"attachment; filename=export.{req.format}"
                }
            )
        
        return {"success": True}
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Export module not available: {str(e)}")


# ============================================================
# AI 辅助 API
# ============================================================

class AIRequest(BaseModel):
    """AI 请求基类"""
    provider: str = "openai"  # openai, gemini, claude
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class AIChatRequest(AIRequest):
    """AI 对话请求"""
    message: str
    context: Optional[dict[str, Any]] = None


class AISuggestRequest(AIRequest):
    """AI 建议请求"""
    current_step: str
    completed_steps: list[str] = []
    context: dict[str, Any] = {}


class AIDescriptionRequest(AIRequest):
    """AI 生成描述请求"""
    var_name: str
    var_type: str
    context: Optional[dict[str, Any]] = None


class AISummaryRequest(AIRequest):
    """AI 摘要请求"""
    data: dict[str, Any]
    aimd_content: Optional[str] = None


class AIAnomalyRequest(AIRequest):
    """AI 异常检测请求"""
    data: dict[str, Any]
    expected_ranges: Optional[dict[str, list]] = None


def _get_ai_provider(req: AIRequest):
    """根据请求获取 AI Provider"""
    from aimd_studio.ai import OpenAIProvider, GeminiProvider, ClaudeProvider
    
    providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
    }
    
    provider_class = providers.get(req.provider, OpenAIProvider)
    return provider_class(api_key=req.api_key, base_url=req.base_url)


@app.post("/api/ai/chat")
async def ai_chat(req: AIChatRequest):
    """AI 对话"""
    try:
        from aimd_studio.ai import AIAssistant
        
        provider = _get_ai_provider(req)
        assistant = AIAssistant(provider)
        
        response = await assistant.chat(req.message, req.context)
        return {"response": response}
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI module not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/suggest-next-step")
async def ai_suggest_next_step(req: AISuggestRequest):
    """AI 建议下一步"""
    try:
        from aimd_studio.ai import AIAssistant
        
        provider = _get_ai_provider(req)
        assistant = AIAssistant(provider)
        
        response = await assistant.suggest_next_step(
            req.current_step,
            req.completed_steps,
            req.context,
        )
        return {"suggestion": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/generate-description")
async def ai_generate_description(req: AIDescriptionRequest):
    """AI 生成变量描述"""
    try:
        from aimd_studio.ai import AIAssistant
        
        provider = _get_ai_provider(req)
        assistant = AIAssistant(provider)
        
        result = await assistant.generate_description(
            req.var_name,
            req.var_type,
            req.context,
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/generate-summary")
async def ai_generate_summary(req: AISummaryRequest):
    """AI 生成实验摘要"""
    try:
        from aimd_studio.ai import AIAssistant
        
        provider = _get_ai_provider(req)
        assistant = AIAssistant(provider)
        
        response = await assistant.generate_summary(req.data, req.aimd_content)
        return {"summary": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/detect-anomalies")
async def ai_detect_anomalies(req: AIAnomalyRequest):
    """AI 检测数据异常"""
    try:
        from aimd_studio.ai import AIAssistant
        
        provider = _get_ai_provider(req)
        assistant = AIAssistant(provider)
        
        # 转换 expected_ranges 格式
        ranges = None
        if req.expected_ranges:
            ranges = {k: tuple(v) for k, v in req.expected_ranges.items()}
        
        anomalies = await assistant.detect_anomalies(req.data, ranges)
        return {"anomalies": anomalies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 辅助函数
# ============================================================

def _serialize_assigned_fields(fields: dict) -> dict:
    """序列化 Assigner 结果，处理 Pydantic 模型"""
    result = {}
    for key, value in fields.items():
        if hasattr(value, "model_dump"):
            result[key] = value.model_dump()
        elif hasattr(value, "__dict__"):
            result[key] = value.__dict__
        else:
            result[key] = value
    return result


# ============================================================
# 启动入口
# ============================================================

def main():
    import uvicorn
    print("🚀 Starting Airalogy Mock Server...")
    print("   Endpoint: http://localhost:4000")
    print("   Docs: http://localhost:4000/docs")
    uvicorn.run(app, host="0.0.0.0", port=4000)


if __name__ == "__main__":
    main()
