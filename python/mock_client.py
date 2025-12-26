"""
Airalogy Client - Mock Version for Extension Backend

Provides local file storage and record management, simulating the cloud SDK.
Adapted from airalogy_mock/client.py
"""

import os
import json
import uuid
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional


def _generate_user_id(name: str = "mock-user") -> str:
    """Generate mock user ID"""
    return f"airalogy.id.user.{name}"


def _generate_record_id(version: int = 1) -> str:
    """Generate mock record ID"""
    return f"airalogy.id.record.{uuid.uuid4()}.v.{version}"


class AiralogyMockClient:
    """
    Airalogy API Client - Mock Implementation
    
    Stores files in <project_dir>/.airalogy_mock/files/
    Stores records in <project_dir>/.airalogy_mock/records/
    """
    
    def __init__(
        self,
        storage_dir: str = ".airalogy_mock",
        protocol_id: str = None,
    ):
        """
        Initialize the mock client.
        
        Args:
            storage_dir: Path to the local storage directory (absolute or relative)
            protocol_id: Protocol ID to use for records
        """
        self.protocol_id = protocol_id or "airalogy.id.lab.mock.protocol.v1"
        
        # Local storage setup
        self.storage_dir = Path(storage_dir)
        self.files_dir = self.storage_dir / "files"
        self.records_dir = self.storage_dir / "records"
        
        # Ensure directories exist
        try:
            self.files_dir.mkdir(parents=True, exist_ok=True)
            self.records_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # might fail if permissions issue, but usually fine in user space
            pass
        
        # Current mock user
        self._current_user = _generate_user_id("vscode-user")
    
    # ========================================================
    # File Operations
    # ========================================================
    
    def upload_file_bytes(self, file_name: str, file_bytes: bytes) -> dict:
        """
        Upload file content (bytes).
        
        Returns:
            {"id": "airalogy.id.file.xxx.ext", "file_name": "..."}
        """
        ext = Path(file_name).suffix.lstrip(".")
        if not ext:
            # Fallback if no extension
            ext = "bin"
        
        file_id = f"airalogy.id.file.{uuid.uuid4()}.{ext}"
        
        # Save file
        file_path = self.files_dir / file_id
        file_path.write_bytes(file_bytes)
        
        # Save metadata
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
        """Upload file content (base64 string)."""
        file_bytes = base64.b64decode(file_base64)
        return self.upload_file_bytes(file_name, file_bytes)
    
    def download_file_bytes(self, file_id: str) -> bytes:
        """Download file content."""
        file_path = self.files_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return file_path.read_bytes()
    
    def get_file_url(self, file_id: str) -> str:
        """Get local file URL."""
        file_path = self.files_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return f"file://{file_path.absolute()}"
    
    # ========================================================
    # Record Operations (Simplified)
    # ========================================================
    
    def create_record(self, data: dict, record_id: str = None) -> dict:
        if record_id is None:
            record_id = _generate_record_id(version=1)
        
        record = {
            "id": record_id,
            "protocol_id": self.protocol_id,
            "data": data,
            "created_at": datetime.now().isoformat(),
            "created_by": str(self._current_user),
        }
        
        record_path = self.records_dir / f"{record_id}.json"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        
        return record

    def list_files(self) -> list:
        files = []
        if self.files_dir.exists():
            for meta_file in self.files_dir.glob("*.meta.json"):
                try:
                    meta = json.loads(meta_file.read_text())
                    files.append(meta)
                except:
                    pass
        return files
