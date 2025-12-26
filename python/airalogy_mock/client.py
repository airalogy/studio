"""
Airalogy Client - 本地文件/记录存储

提供本地文件存储和记录管理，用于开发测试。
支持完整的 Airalogy Record 格式。
"""

import os
import json
import uuid
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


def _generate_user_id(name: str = "mock-user") -> str:
    """生成模拟用户 ID"""
    return f"airalogy.id.user.{name}"


def _generate_record_uuid() -> str:
    """生成记录 UUID"""
    return str(uuid.uuid4())


def _generate_file_id(ext: str) -> str:
    """生成文件 ID"""
    return f"airalogy.id.file.{uuid.uuid4()}.{ext}"


def _calculate_sha1(data: dict) -> str:
    """计算数据的 SHA1 哈希"""
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(json_str.encode()).hexdigest()


class RecordSession:
    """
    Record 会话 - 管理单个实验记录的填写过程
    
    当启动 Record 模式时创建，用于：
    - 跟踪所有 var/step/check 的值
    - 自动生成完整的 Record JSON
    - 支持保存和加载
    """
    
    def __init__(
        self,
        client: "Airalogy",
        protocol_id: str,
        lab_id: str = "mock-lab",
        project_id: str = "mock-project",
        protocol_version: str = "1.0.0",
        record_id: Optional[str] = None,
    ):
        self.client = client
        self.protocol_id = protocol_id
        self.lab_id = lab_id
        self.project_id = project_id
        self.protocol_version = protocol_version
        
        # 生成或使用提供的 record_id
        self._record_uuid = record_id or _generate_record_uuid()
        self._record_version = 1
        
        # 数据存储
        self._var_data: dict[str, Any] = {}
        self._step_data: dict[str, dict] = {}
        self._check_data: dict[str, dict] = {}
        
        # 元数据
        self._created_at = datetime.now().isoformat()
        self._created_by = client.get_current_user()
        self._updated_at = self._created_at
        self._record_num = 1
        
        self._is_active = True
    
    @property
    def airalogy_record_id(self) -> str:
        """完整的 Airalogy Record ID"""
        return f"airalogy.id.record.{self._record_uuid}.v.{self._record_version}"
    
    @property
    def airalogy_protocol_id(self) -> str:
        """完整的 Airalogy Protocol ID"""
        return f"airalogy.id.lab.{self.lab_id}.project.{self.project_id}.protocol.{self.protocol_id}.v.{self.protocol_version}"
    
    # ========================================================
    # 变量操作
    # ========================================================
    
    def set_var(self, var_id: str, value: Any) -> None:
        """设置变量值"""
        self._var_data[var_id] = value
        self._updated_at = datetime.now().isoformat()
    
    def get_var(self, var_id: str, default: Any = None) -> Any:
        """获取变量值"""
        return self._var_data.get(var_id, default)
    
    def set_vars(self, data: dict[str, Any]) -> None:
        """批量设置变量"""
        self._var_data.update(data)
        self._updated_at = datetime.now().isoformat()
    
    def get_all_vars(self) -> dict[str, Any]:
        """获取所有变量"""
        return dict(self._var_data)
    
    # ========================================================
    # 步骤操作
    # ========================================================
    
    def set_step(
        self,
        step_id: str,
        checked: Optional[bool] = None,
        annotation: str = "",
    ) -> None:
        """设置步骤状态"""
        self._step_data[step_id] = {
            "checked": checked,
            "annotation": annotation,
        }
        self._updated_at = datetime.now().isoformat()
    
    def get_step(self, step_id: str) -> Optional[dict]:
        """获取步骤状态"""
        return self._step_data.get(step_id)
    
    def complete_step(self, step_id: str, annotation: str = "") -> None:
        """标记步骤完成"""
        self.set_step(step_id, checked=True, annotation=annotation)
    
    def get_all_steps(self) -> dict[str, dict]:
        """获取所有步骤"""
        return dict(self._step_data)
    
    # ========================================================
    # 检查点操作
    # ========================================================
    
    def set_check(
        self,
        check_id: str,
        checked: bool,
        annotation: str = "",
    ) -> None:
        """设置检查点状态"""
        self._check_data[check_id] = {
            "checked": checked,
            "annotation": annotation,
        }
        self._updated_at = datetime.now().isoformat()
    
    def get_check(self, check_id: str) -> Optional[dict]:
        """获取检查点状态"""
        return self._check_data.get(check_id)
    
    def pass_check(self, check_id: str, annotation: str = "") -> None:
        """通过检查点"""
        self.set_check(check_id, checked=True, annotation=annotation)
    
    def fail_check(self, check_id: str, annotation: str = "") -> None:
        """未通过检查点"""
        self.set_check(check_id, checked=False, annotation=annotation)
    
    def get_all_checks(self) -> dict[str, dict]:
        """获取所有检查点"""
        return dict(self._check_data)
    
    # ========================================================
    # Record 生成
    # ========================================================
    
    def to_record(self) -> dict:
        """生成完整的 Airalogy Record JSON"""
        data_block = {
            "var": self._var_data,
            "step": self._step_data,
            "check": self._check_data,
        }
        
        record = {
            "airalogy_record_id": self.airalogy_record_id,
            "record_id": self._record_uuid,
            "record_version": self._record_version,
            "metadata": {
                "airalogy_protocol_id": self.airalogy_protocol_id,
                "lab_id": self.lab_id,
                "project_id": self.project_id,
                "protocol_id": self.protocol_id,
                "protocol_version": self.protocol_version,
                "record_num": self._record_num,
                "record_current_version_submission_time": self._updated_at,
                "record_current_version_submission_user_id": self.client.get_current_user(),
                "record_initial_version_submission_time": self._created_at,
                "record_initial_version_submission_user_id": self._created_by,
                "sha1": _calculate_sha1(data_block),
            },
            "data": data_block,
        }
        
        return record
    
    def to_json(self, indent: int = 2) -> str:
        """生成 JSON 字符串"""
        return json.dumps(self.to_record(), ensure_ascii=False, indent=indent)
    
    # ========================================================
    # 保存和加载
    # ========================================================
    
    def save(self) -> str:
        """保存 Record 到本地存储，返回 record_id"""
        record = self.to_record()
        record_path = self.client.records_dir / f"{self.airalogy_record_id}.json"
        record_path.write_text(self.to_json(), encoding="utf-8")
        return self.airalogy_record_id
    
    def increment_version(self) -> None:
        """增加版本号（用于更新）"""
        self._record_version += 1
        self._updated_at = datetime.now().isoformat()
    
    @classmethod
    def load(cls, client: "Airalogy", record_id: str) -> "RecordSession":
        """从本地存储加载 Record"""
        record_path = client.records_dir / f"{record_id}.json"
        if not record_path.exists():
            raise FileNotFoundError(f"Record not found: {record_id}")
        
        record = json.loads(record_path.read_text(encoding="utf-8"))
        
        # 解析 record_id
        # 格式: airalogy.id.record.<uuid>.v.<version>
        parts = record["airalogy_record_id"].split(".")
        record_uuid = parts[3]
        record_version = int(parts[5])
        
        metadata = record["metadata"]
        
        session = cls(
            client=client,
            protocol_id=metadata["protocol_id"],
            lab_id=metadata["lab_id"],
            project_id=metadata["project_id"],
            protocol_version=metadata["protocol_version"],
            record_id=record_uuid,
        )
        
        # 恢复数据
        session._record_version = record_version
        session._var_data = record["data"].get("var", {})
        session._step_data = record["data"].get("step", {})
        session._check_data = record["data"].get("check", {})
        session._created_at = metadata["record_initial_version_submission_time"]
        session._created_by = metadata["record_initial_version_submission_user_id"]
        session._updated_at = metadata["record_current_version_submission_time"]
        session._record_num = metadata.get("record_num", 1)
        
        return session


class Airalogy:
    """
    Airalogy 客户端 - 本地模拟版
    
    文件存储在 .airalogy_mock/files/ 目录
    记录存储在 .airalogy_mock/records/ 目录
    
    支持 Record 模式：
        client = Airalogy()
        session = client.start_record_session(protocol_id="my_protocol")
        session.set_var("var_1", "value")
        session.complete_step("step_1")
        session.pass_check("check_1")
        session.save()
    """
    
    def __init__(
        self,
        endpoint: str = None,
        api_key: str = None,
        protocol_id: str = None,
        storage_dir: str = None,
    ):
        """
        初始化客户端
        
        Args:
            endpoint: API 端点 (模拟模式下忽略)
            api_key: API 密钥 (模拟模式下忽略)
            protocol_id: 协议 ID
            storage_dir: 本地存储目录，默认 .airalogy_mock
        """
        self.endpoint = endpoint or os.environ.get("AIRALOGY_ENDPOINT", "http://localhost:4000")
        self.api_key = api_key or os.environ.get("AIRALOGY_API_KEY", "mock-api-key")
        self.protocol_id = protocol_id or os.environ.get(
            "AIRALOGY_PROTOCOL_ID",
            "airalogy.id.lab.mock.project.dev.protocol.test.v.0.0.1"
        )
        
        # 本地存储目录 - 优先使用参数，然后环境变量，最后默认值
        self.storage_dir = Path(
            storage_dir or 
            os.environ.get("AIRALOGY_STORAGE_DIR") or 
            ".airalogy_mock"
        )
        self.files_dir = self.storage_dir / "files"
        self.records_dir = self.storage_dir / "records"
        
        # 确保目录存在
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前用户 (模拟)
        self._current_user = _generate_user_id("mock-user")
        
        # 当前活跃的 Record Session
        self._active_session: Optional[RecordSession] = None
        self._active_session_file = self.storage_dir / "active_session.id"
        
        # 尝试恢复活跃会话
        self._restore_active_session()

    def _restore_active_session(self):
        """尝试从磁盘恢复活跃会话"""
        if self._active_session_file.exists():
            try:
                record_id = self._active_session_file.read_text().strip()
                if record_id:
                    # 尝试加载
                    try:
                        self.load_record_session(record_id)
                        # print(f"Restored active session: {record_id}")
                    except Exception:
                        # 加载失败（可能被删除了），清除标记
                        self._clear_active_session_file()
            except Exception:
                pass

    def _save_active_session_id(self, record_id: str):
        """保存活跃会话 ID"""
        try:
            self._active_session_file.write_text(record_id)
        except Exception:
            pass

    def _clear_active_session_file(self):
        """清除活跃会话标记"""
        try:
            if self._active_session_file.exists():
                self._active_session_file.unlink()
        except Exception:
            pass
    
    # ========================================================
    # Record Session 管理
    # ========================================================
    
    def start_record_session(
        self,
        protocol_id: str,
        lab_id: str = "mock-lab",
        project_id: str = "mock-project",
        protocol_version: str = "1.0.0",
    ) -> RecordSession:
        """
        启动 Record 模式，创建新的记录会话
        """
        self._active_session = RecordSession(
            client=self,
            protocol_id=protocol_id,
            lab_id=lab_id,
            project_id=project_id,
            protocol_version=protocol_version,
        )
        
        # 立即保存初始状态，确保重启后能找到
        self._active_session.save()
        self._save_active_session_id(self._active_session.airalogy_record_id)
        
        return self._active_session
    
    def load_record_session(self, record_id: str) -> RecordSession:
        """
        加载已有的 Record 会话
        """
        self._active_session = RecordSession.load(self, record_id)
        self._save_active_session_id(self._active_session.airalogy_record_id)
        return self._active_session
    
    def get_active_session(self) -> Optional[RecordSession]:
        """获取当前活跃的 Record Session"""
        return self._active_session
    
    def end_record_session(self, save: bool = True) -> Optional[str]:
        """
        结束 Record 模式
        """
        if self._active_session is None:
            return None
        
        record_id = None
        if save:
            record_id = self._active_session.save()
        
        self._active_session = None
        self._clear_active_session_file()
        
        return record_id
    
    # ========================================================
    # 文件操作
    # ========================================================
    
    def upload_file_bytes(self, file_name: str, file_bytes: bytes) -> dict:
        """
        上传文件 (bytes)
        
        Args:
            file_name: 文件名 (必须包含扩展名)
            file_bytes: 文件内容
        
        Returns:
            {"id": "airalogy.id.file.xxx.ext", "file_name": "..."}
        """
        ext = Path(file_name).suffix.lstrip(".")
        if not ext:
            raise ValueError("file_name must include extension")
        
        file_id = _generate_file_id(ext)
        
        # 保存文件
        file_path = self.files_dir / file_id
        file_path.write_bytes(file_bytes)
        
        # 保存元数据
        meta_path = self.files_dir / f"{file_id}.meta.json"
        meta_path.write_text(json.dumps({
            "id": file_id,
            "file_name": file_name,
            "size": len(file_bytes),
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": str(self._current_user),
        }, ensure_ascii=False, indent=2))
        
        return {"id": file_id, "file_name": file_name}
    
    def upload_file_base64(self, file_name: str, file_base64: str) -> dict:
        """上传文件 (base64)"""
        file_bytes = base64.b64decode(file_base64)
        return self.upload_file_bytes(file_name, file_bytes)
    
    def download_file_bytes(self, file_id: str) -> bytes:
        """下载文件 (bytes)"""
        file_path = self.files_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return file_path.read_bytes()
    
    def download_file_base64(self, file_id: str) -> str:
        """下载文件 (base64)"""
        file_bytes = self.download_file_bytes(file_id)
        return base64.b64encode(file_bytes).decode()
    
    def get_file_url(self, file_id: str) -> str:
        """获取文件临时 URL (本地模式返回 file:// URL)"""
        file_path = self.files_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return f"file://{file_path.absolute()}"
    
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        file_path = self.files_dir / file_id
        meta_path = self.files_dir / f"{file_id}.meta.json"
        
        deleted = False
        if file_path.exists():
            file_path.unlink()
            deleted = True
        if meta_path.exists():
            meta_path.unlink()
        
        return deleted
    
    def list_files(self) -> list[dict]:
        """列出所有文件"""
        files = []
        for meta_file in self.files_dir.glob("*.meta.json"):
            meta = json.loads(meta_file.read_text())
            files.append(meta)
        return files
    
    # ========================================================
    # 记录操作 (兼容旧 API)
    # ========================================================
    
    def create_record(self, data: dict, record_id: str = None) -> dict:
        """
        创建记录 (兼容旧 API)
        
        推荐使用 start_record_session() 来创建完整格式的记录
        """
        # 检查是否是完整的 Record 格式
        if "data" in data and ("var" in data["data"] or "step" in data["data"] or "check" in data["data"]):
            # 已经是完整格式，直接保存
            if record_id is None:
                record_uuid = _generate_record_uuid()
                record_id = f"airalogy.id.record.{record_uuid}.v.1"
            
            if "airalogy_record_id" not in data:
                data["airalogy_record_id"] = record_id
            if "record_id" not in data:
                data["record_id"] = record_id.split(".")[3]
            if "record_version" not in data:
                data["record_version"] = 1
            
            record_path = self.records_dir / f"{record_id}.json"
            record_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            return data
        
        # 旧格式，包装成简单记录
        if record_id is None:
            record_uuid = _generate_record_uuid()
            record_id = f"airalogy.id.record.{record_uuid}.v.1"
        
        record = {
            "airalogy_record_id": record_id,
            "record_id": record_id.split(".")[3] if "." in record_id else record_id,
            "record_version": 1,
            "metadata": {
                "airalogy_protocol_id": self.protocol_id,
                "created_at": datetime.now().isoformat(),
                "created_by": str(self._current_user),
                "updated_at": datetime.now().isoformat(),
            },
            "data": {
                "var": data,
                "step": {},
                "check": {},
            },
        }
        
        record_path = self.records_dir / f"{record_id}.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        
        return record
    
    def update_record(self, record_id: str, data: dict) -> dict:
        """更新记录"""
        record_path = self.records_dir / f"{record_id}.json"
        if not record_path.exists():
            raise FileNotFoundError(f"Record not found: {record_id}")
        
        record = json.loads(record_path.read_text())
        
        # 支持更新 var/step/check
        if "var" in data:
            record["data"]["var"].update(data["var"])
        if "step" in data:
            record["data"]["step"].update(data["step"])
        if "check" in data:
            record["data"]["check"].update(data["check"])
        
        # 如果直接传入字段，更新到 var
        for key, value in data.items():
            if key not in ("var", "step", "check"):
                record["data"]["var"][key] = value
        
        # 更新元数据
        if "metadata" in record:
            record["metadata"]["updated_at"] = datetime.now().isoformat()
            record["metadata"]["record_current_version_submission_time"] = datetime.now().isoformat()
        
        # 增加版本号
        record["record_version"] = record.get("record_version", 1) + 1
        old_id = record["airalogy_record_id"]
        new_id = old_id.rsplit(".v.", 1)[0] + f".v.{record['record_version']}"
        record["airalogy_record_id"] = new_id
        
        # 重新计算 SHA1
        if "metadata" in record:
            record["metadata"]["sha1"] = _calculate_sha1(record["data"])
        
        # 保存到新文件名
        new_record_path = self.records_dir / f"{new_id}.json"
        new_record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        
        # 可选：保留旧版本或删除
        # record_path.unlink()  # 删除旧版本
        
        return record
    
    def get_record(self, record_id: str) -> dict:
        """获取单条记录"""
        record_path = self.records_dir / f"{record_id}.json"
        if not record_path.exists():
            raise FileNotFoundError(f"Record not found: {record_id}")
        return json.loads(record_path.read_text())
    
    def download_records_json(self, record_ids: list[str]) -> str:
        """下载多条记录 (JSON 字符串)"""
        records = []
        for rid in record_ids:
            try:
                record = self.get_record(rid)
                records.append(record)
            except FileNotFoundError:
                pass
        return json.dumps(records, ensure_ascii=False)
    
    def list_records(self) -> list[dict]:
        """列出所有记录"""
        records = []
        for record_file in self.records_dir.glob("*.json"):
            try:
                record = json.loads(record_file.read_text())
                records.append({
                    "id": record.get("airalogy_record_id", record_file.stem),
                    "alias": record.get("alias", ""),
                    "protocol_id": record.get("metadata", {}).get("airalogy_protocol_id"),
                    "created_at": record.get("metadata", {}).get("record_initial_version_submission_time"),
                    "updated_at": record.get("metadata", {}).get("record_current_version_submission_time"),
                    "version": record.get("record_version", 1),
                })
            except Exception:
                pass
        return records
    
    def delete_record(self, record_id: str) -> bool:
        """删除记录"""
        record_path = self.records_dir / f"{record_id}.json"
        if record_path.exists():
            record_path.unlink()
            return True
        return False
    
    def rename_record(self, record_id: str, alias: str) -> bool:
        """设置记录别名"""
        record_path = self.records_dir / f"{record_id}.json"
        if record_path.exists():
            with open(record_path, 'r', encoding='utf-8') as f:
                record = json.load(f)
            record["alias"] = alias
            with open(record_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            return True
        return False
    
    # ========================================================
    # 上下文信息
    # ========================================================
    
    def get_current_user(self) -> str:
        """获取当前用户"""
        return str(self._current_user)
    
    def set_current_user(self, user_id: str) -> None:
        """设置当前用户"""
        if not user_id.startswith("airalogy.id.user."):
            user_id = f"airalogy.id.user.{user_id}"
        self._current_user = user_id
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        return datetime.now().isoformat()
    
    def get_protocol_id(self) -> str:
        """获取当前协议 ID"""
        return self.protocol_id
