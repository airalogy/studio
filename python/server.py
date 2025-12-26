import json
import os
import sys
import importlib.util
from datetime import datetime
from typing import Any, Dict, Optional, Type

# Version info
AIMD_SERVER_VERSION = "0.4.1"

# Set default Airalogy environment variables if not set
# This allows assigner.py to load Airalogy client without manual configuration
# Real operations will use mock client; these are just placeholders for initialization
if not os.environ.get("AIRALOGY_ENDPOINT"):
    os.environ["AIRALOGY_ENDPOINT"] = "http://localhost:8765"
if not os.environ.get("AIRALOGY_API_KEY"):
    os.environ["AIRALOGY_API_KEY"] = "mock-api-key"
if not os.environ.get("AIRALOGY_PROTOCOL_ID"):
    os.environ["AIRALOGY_PROTOCOL_ID"] = "mock-protocol-id"

# Try to import airalogy SDK components
try:
    from airalogy.assigner import DefaultAssigner
    from airalogy.models import CheckValue
    HAS_AIRALOGY = True
except ImportError:
    HAS_AIRALOGY = False

# Ensure the current directory is in sys.path (should be by default for the main script)
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from airalogy_mock.client import Airalogy as MockAiralogy
    HAS_MOCK = True
    
    # Monkey-patch the real airalogy SDK to use our mock client
    # This allows assigner.py's `from airalogy import Airalogy` to get our local storage version
    try:
        import airalogy
        import airalogy.airalogy
        airalogy.Airalogy = MockAiralogy
        airalogy.airalogy.Airalogy = MockAiralogy
        print(f"[{datetime.now().isoformat()}] Patched airalogy SDK with mock client", file=sys.stderr, flush=True)
    except ImportError:
        pass  # airalogy SDK not installed, mock client still works standalone
except ImportError:
    HAS_MOCK = False
    MockAiralogy = None

# Expose MockAiralogy as Airalogy for this module's use
Airalogy = MockAiralogy

def log_stderr(message: str) -> None:
    """Log to stderr (will be captured by VS Code output channel)."""
    print(f"[{datetime.now().isoformat()}] {message}", file=sys.stderr, flush=True)


class ProjectManager:
    """Manages dynamic loading of model.py and assigner.py."""
    
    def __init__(self):
        self.current_project_path: Optional[str] = None
        self.var_model: Optional[Type] = None
        self.has_assigners = False
        self.mock_client = Airalogy() if HAS_MOCK else None
        self.overrides: Dict[str, Any] = {}  # Runtime variable overrides

    def load_project(self, project_path: str) -> bool:
        """Load variables and assigners from a project directory.
        
        Note: Always reloads to pick up file changes (no caching).
        """
        log_stderr(f"Loading project from: {project_path}")
        
        # Add project path to sys.path for imports
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
        
        # Clear cached modules to force reload
        for mod_name in ['model', 'assigner']:
            if mod_name in sys.modules:
                del sys.modules[mod_name]
        
        # Also clear any airalogy assigner registry if we're reloading
        if HAS_AIRALOGY:
            try:
                from airalogy.assigner import DefaultAssigner
                # Reset the assigner registry to avoid duplicate registrations
                # The registry is stored in assigned_info and dependent_info
                if hasattr(DefaultAssigner, 'assigned_info'):
                    DefaultAssigner.assigned_info.clear()
                if hasattr(DefaultAssigner, 'dependent_info'):
                    DefaultAssigner.dependent_info.clear()
                log_stderr("Cleared assigner registry")
            except Exception as e:
                log_stderr(f"Could not reset assigner registry: {e}")
        
        try:
            # Initialize Mock Client for this project
            storage_dir = os.path.join(project_path, ".airalogy_mock")
            
            # CRITICAL: Set env var so that Airalogy() created in assigner.py uses same storage
            os.environ["AIRALOGY_STORAGE_DIR"] = storage_dir
            
            # Only recreate client if path changed or not exists, to preserve active sessions
            if (not self.mock_client or self.current_project_path != project_path) and HAS_MOCK and Airalogy:
                self.mock_client = Airalogy(storage_dir=storage_dir)
            
            # Reset overrides on project reload
            self.overrides = {}
            
            # If there is an active session restored by mock client, sync its variables to overrides
            if self.mock_client:
                active_session = self.mock_client.get_active_session()
                if active_session:
                    session_vars = active_session.get_all_vars()
                    self.overrides.update(session_vars)
                    log_stderr(f"Restored {len(session_vars)} variables from active session")

            # Load model.py (or alternative model files)
            # Try multiple possible model filenames
            model_filenames = ["model.py", "tmp_aimd_model.py", "var_model.py"]
            model_path = None
            for filename in model_filenames:
                path_candidate = os.path.join(project_path, filename)
                if os.path.exists(path_candidate):
                    model_path = path_candidate
                    log_stderr(f"Found model file: {filename}")
                    break
            
            if model_path:
                spec = importlib.util.spec_from_file_location("model", model_path)
                if spec and spec.loader:
                    model_module = importlib.util.module_from_spec(spec)
                    sys.modules['model'] = model_module  # Register in sys.modules
                    spec.loader.exec_module(model_module)
                    self.var_model = getattr(model_module, "VarModel", None)
                    log_stderr(f"Loaded VarModel: {self.var_model is not None}")
            
            # Load assigner.py (triggers @assigner decorators)
            assigner_path = os.path.join(project_path, "assigner.py")
            if os.path.exists(assigner_path):
                try:
                    spec = importlib.util.spec_from_file_location("assigner", assigner_path)
                    if spec and spec.loader:
                        assigner_module = importlib.util.module_from_spec(spec)
                        sys.modules['assigner'] = assigner_module  # Register in sys.modules
                        spec.loader.exec_module(assigner_module)
                        self.has_assigners = True
                        log_stderr(f"Loaded assigner module, functions: {[n for n in dir(assigner_module) if not n.startswith('_')]}")
                        
                        # Check if assigners were registered
                        if HAS_AIRALOGY:
                            from airalogy.assigner import DefaultAssigner
                            all_fields = DefaultAssigner.all_assigned_fields()
                            log_stderr(f"Registered assigners after load: {list(all_fields.keys())}")
                except Exception as e:
                    log_stderr(f"Error loading assigner.py: {e}")
                    import traceback
                    log_stderr(traceback.format_exc())
            
            self.current_project_path = project_path
            return True
        except Exception as e:
            log_stderr(f"Error loading project: {e}")
            return False

    def update_variable(self, field_name: str, value: Any) -> bool:
        """Update a variable's runtime value (in overrides)."""
        log_stderr(f"Updating variable {field_name} = {str(value)[:50]}...")
        self.overrides[field_name] = value
        return True

    def get_variables_metadata(self) -> Dict[str, Any]:
        """Extract metadata and default values from VarModel."""
        if not self.var_model:
            return {}
            
        try:
            metadata = {}
            
            # 1. Get schema for metadata (title, description, type, constraints)
            if hasattr(self.var_model, "model_json_schema"):
                schema = self.var_model.model_json_schema()
                properties = schema.get("properties", {})
                
                for name, prop in properties.items():
                    metadata[name] = {
                        "title": prop.get("title", name),
                        "description": prop.get("description", ""),
                        "type": prop.get("type", "any"),
                        "default": prop.get("default"),
                        "constraints": {
                            k: v for k, v in prop.items() 
                            if k in ["minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "pattern", "minLength", "maxLength"]
                        }
                    }
            
            # 1.5 Enhance with python type names (for custom UI components like FileIdPNG)
            # This is critical for the frontend to know which component to render
            if hasattr(self.var_model, "model_fields"):
                for name, field in self.var_model.model_fields.items():
                    if name in metadata:
                        # Extract type annotation
                        annotation = field.annotation
                        
                        # Convert annotation to string representation
                        # Handle Optional[T] -> T
                        str_type = str(annotation)
                        raw_str = str_type # Keep raw for detection
                        
                        # Debug log raw annotation
                        if "FileId" in str_type or "AiralogyMarkdown" in str_type:
                            log_stderr(f"Type processing for {name}: {str_type}")

                        # Clean up "typing.Optional" or "Optional" wrapper
                        if "typing.Optional[" in str_type:
                            str_type = str_type.replace("typing.Optional[", "").rsplit("]", 1)[0]
                        elif "Optional[" in str_type:
                            str_type = str_type.replace("Optional[", "").rsplit("]", 1)[0]
                        
                        # Clean up union syntax "Type | None" (Python 3.10+)
                        if " | None" in str_type:
                            str_type = str_type.replace(" | None", "")
                        
                        # Clean up module prefixes (e.g. <class 'airalogy.types.FileIdPNG'> -> FileIdPNG)
                        if "<class" in str_type:
                             str_type = str_type.split("'")[1]
                        
                        # Remove package path prefix
                        if "." in str_type:
                            str_type = str_type.split(".")[-1]
                            
                        # If it's one of our special types, use it explicitly
                        special_types = [
                            "FileIdPNG", "FileIdJPG", "FileIdTIFF", "FileIdPDF", "FileIdCSV", "FileIdMP4",
                            "RecordId", "AiralogyMarkdown", "PyStr", "JsStr", "TsStr", "IgnoreStr",
                            "UserName", "CurrentTime", "CurrentRecordId", "VersionStr"
                        ]
                        
                        # Check if matches any special type
                        detected = False
                        
                        # 1. Try simple substring match in raw annotation first (safest and most robust for Annotated types)
                        # This fixes issue where aggressive cleaning stripped info from Pydantic Annotated types
                        for st in special_types:
                            if st in raw_str:
                                metadata[name]["varType"] = st
                                log_stderr(f"Detected special type for {name} (Raw Match): {st}")
                                detected = True
                                break
                        
                        if not detected:
                            # 2. Fallback to cleaned type match
                            for st in special_types:
                                if st == str_type or st in str_type:
                                    metadata[name]["varType"] = st
                                    log_stderr(f"Detected special type for {name} (Cleaned Match): {st}")
                                    break
                        
                        # Also save the raw python type if useful
                        if "varType" not in metadata[name]:
                             metadata[name]["pythonType"] = str_type
                             if "FileId" in str_type: # Debug fallback
                                 log_stderr(f"Failed to match special type for {name}. Cleaned type: {str_type}")
            
            # 2. Instantiate model to get actual default values (including factory defaults)
            try:
                # Create instance with minimal required fields
                # For fields that require values, we pass empty/mock values
                instance = self.var_model.model_construct()
                
                # Get actual values from the instance
                if hasattr(instance, "model_dump"):
                    defaults = instance.model_dump()
                    for name, value in defaults.items():
                        if name in metadata:
                            # Store actual default value (for tables, lists, etc.)
                            metadata[name]["default_value"] = value
            except Exception as e:
                log_stderr(f"Could not instantiate model for defaults: {e}")
            
            # 3. APPLY OVERRIDES (The "Sync" Logic)
            # If we have runtime overrides, they should take precedence as the "default value"
            # for the UI to render.
            if self.overrides:
                for name, value in self.overrides.items():
                    if name in metadata:
                        metadata[name]["default_value"] = value
                        metadata[name]["default"] = value # Also update 'default' key used by some UI
                        log_stderr(f"Applied override for {name}")

            return metadata
        except Exception as e:
            log_stderr(f"Error extracting metadata: {e}")
            
        return {}

    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform calculations using airalogy assigners."""
        
        # Merge overrides into data? 
        # Usually data passed here comes from the frontend form state.
        # But if the frontend state is "incomplete", maybe use overrides as fallback?
        # For now, trust the data passed, but ensure overrides are available if needed.
        
        if not HAS_AIRALOGY:
            log_stderr("Airalogy SDK not available for calculation")
            # Even if no SDK, we might want to return overrides if any?
            return {"data": data, "calculated_fields": {}}
        
        if not self.has_assigners:
            log_stderr("No assigners loaded")
            return {"data": data, "calculated_fields": {}}
            
        try:
            from airalogy.assigner import DefaultAssigner
            
            log_stderr(f"Running calculations with data keys: {list(data.keys())[:5]}...")
            
            # Get all registered assigned fields
            all_fields = DefaultAssigner.all_assigned_fields()
            
            calculated_fields: Dict[str, Any] = {}
            result_data = dict(data)
            
            # Execute all 'auto' mode assigners
            for field_name, field_info in all_fields.items():
                if field_info.get("mode") == "auto":
                    try:
                        # log_stderr(f"Executing assigner for: {field_name}")
                        result = DefaultAssigner.assign(field_name, result_data)
                        
                        if result.success and result.assigned_fields:
                            for key, value in result.assigned_fields.items():
                                # Handle CheckValue objects by converting to dict
                                if hasattr(value, 'checked'):
                                    value = {
                                        "checked": value.checked,
                                        "annotation": getattr(value, 'annotation', '')
                                    }
                                calculated_fields[key] = value
                                result_data[key] = value
                                # log_stderr(f"  Assigned {key}")
                        elif result.error_message:
                            pass
                            # log_stderr(f"  Error for {field_name}: {result.error_message}")
                    except Exception as e:
                        log_stderr(f"  Error executing {field_name}: {e}")
            
            return {
                "data": result_data,
                "calculated_fields": calculated_fields
            }
        except Exception as e:
            log_stderr(f"Calculation error: {e}")
            return {"data": data, "calculated_fields": {}, "error": str(e)}

    def get_assigners_metadata(self) -> Dict[str, Any]:
        """Return metadata about all registered assigners."""
        log_stderr(f"get_assigners_metadata called: HAS_AIRALOGY={HAS_AIRALOGY}, has_assigners={self.has_assigners}")
        
        if not HAS_AIRALOGY:
            log_stderr("Airalogy SDK not available")
            return {}
        
        if not self.has_assigners:
            log_stderr("No assigner module loaded")
            return {}
        
        try:
            from airalogy.assigner import DefaultAssigner
            all_fields = DefaultAssigner.all_assigned_fields()
            log_stderr(f"DefaultAssigner.all_assigned_fields() returned {len(all_fields)} fields: {list(all_fields.keys())}")
            
            result = {}
            for field, info in all_fields.items():
                mode = info.get("mode", "auto")
                result[field] = {
                    "mode": mode,
                    "dependent_fields": info.get("dependent_fields", []),
                    "readonly": mode.endswith("_readonly"),
                }
            return result
        except Exception as e:
            log_stderr(f"Error getting assigners: {e}")
            import traceback
            log_stderr(traceback.format_exc())
            return {}

    def trigger_assigner(self, field_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manually trigger a specific assigner."""
        if not HAS_AIRALOGY or not self.has_assigners:
            return {"success": False, "error": "Airalogy not available"}
        
        try:
            from airalogy.assigner import DefaultAssigner
            log_stderr(f"Triggering assigner for: {field_name}")
            
            result = DefaultAssigner.assign(field_name, data)
            
            if result.success and result.assigned_fields:
                calculated = {}
                for key, value in result.assigned_fields.items():
                    if hasattr(value, 'checked'):
                        value = {
                            "checked": value.checked,
                            "annotation": getattr(value, 'annotation', '')
                        }
                    calculated[key] = value
                return {"success": True, "calculated_fields": calculated}
            else:
                return {"success": False, "error": result.error_message or "Unknown error"}
        except Exception as e:
            log_stderr(f"Error triggering assigner: {e}")
            return {"success": False, "error": str(e)}


# Global project manager
manager = ProjectManager()


def handle_request(method: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Route JSON-RPC method calls to handler functions."""
    params = params or {}
    
    if method == "version":
        # Get airalogy SDK version if available
        airalogy_version = None
        try:
            import airalogy
            airalogy_version = getattr(airalogy, '__version__', 'unknown')
        except ImportError:
            pass
        
        return {
            "server_version": AIMD_SERVER_VERSION,
            "airalogy_sdk_version": airalogy_version,
            "has_airalogy": HAS_AIRALOGY,
            "has_mock": HAS_MOCK,
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
    
    elif method == "hello":
        name = params.get("name", "World")
        return {
            "message": f"Hello, {name}! 🐍 Backend enhanced.",
            "timestamp": datetime.now().isoformat()
        }
    
    elif method == "load_project":
        path = params.get("path")
        if not path:
            raise ValueError("Missing 'path' parameter")
        success = manager.load_project(path)
        return {"success": success}
        
    elif method == "get_variables":
        log_stderr("get_variables called")
        result = manager.get_variables_metadata()
        log_stderr(f"get_variables returning {len(result)} fields")
        return result
        
    elif method == "calculate":
        data = params.get("data", {})
        result = manager.calculate(data)
        return result
    
    elif method == "get_assigners":
        return manager.get_assigners_metadata()
    
    elif method == "trigger_assigner":
        field_name = params.get("field_name")
        data = params.get("data", {})
        if not field_name:
            raise ValueError("Missing 'field_name' parameter")
        return manager.trigger_assigner(field_name, data)
    
    # --- New Methods for Files and Variables ---
    
    elif method == "file:upload":
        if not manager.mock_client:
            raise ValueError("Mock client not initialized. Load a project first.")
        
        file_path = params.get("filePath")
        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"Invalid file path: {file_path}")
        
        try:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                content = f.read()
            
            result = manager.mock_client.upload_file_bytes(file_name, content)
            return result
        except Exception as e:
            raise ValueError(f"Upload failed: {e}")
            
    elif method == "variable:update":
        field_name = params.get("fieldName")
        value = params.get("value")
        if not field_name:
            raise ValueError("Missing 'fieldName'")
        
        success = manager.update_variable(field_name, value)
        return {"success": success}
    
    elif method == "shutdown":
        sys.exit(0)
    
    # --- Record Session Methods ---

    elif method == "session_start":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        protocol_id = params.get("protocol_id", "mock-protocol")
        session = manager.mock_client.start_record_session(protocol_id=protocol_id)
        return {
            "success": True, 
            "record_id": session.airalogy_record_id,
            "protocol_id": session.airalogy_protocol_id
        }

    elif method == "session_end":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        save = params.get("save", True)
        record_id = manager.mock_client.end_record_session(save=save)
        return {
            "success": True, 
            "saved": save,
            "record_id": record_id
        }

    elif method == "session_upload":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        # New dedicated session upload endpoint
        var_id = params.get("var_id")
        file_name = params.get("file_name")
        file_base64 = params.get("file_base64")
        
        if not var_id or not file_name or not file_base64:
            raise ValueError("Missing parameters for session_upload")
            
        session = manager.mock_client.get_active_session()
        if not session:
            raise ValueError("No active session")
            
        # 1. Upload file
        upload_result = manager.mock_client.upload_file_base64(file_name, file_base64)
        file_id = upload_result["id"]
        
        # 2. Set variable to file_id (crucial link!)
        session.set_var(var_id, file_id)
        
        return {
            "success": True,
            "var_id": var_id,
            "file_id": file_id
        }

    elif method == "session_set_var":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
            
        var_id = params.get("var_id")
        value = params.get("value")
        
        session = manager.mock_client.get_active_session()
        if not session:
            raise ValueError("No active session")
            
        session.set_var(var_id, value)
        return {"success": True}

    elif method == "list_records":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        return manager.mock_client.list_records()

    elif method == "session_load":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        record_id = params.get("record_id")
        if not record_id:
            raise ValueError("Missing 'record_id'")
            
        session = manager.mock_client.load_record_session(record_id)
        return {
            "success": True, 
            "record_id": session.airalogy_record_id,
            "protocol_id": session.airalogy_protocol_id,
            "data": session.to_record()
        }

    elif method == "delete_record":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        record_id = params.get("record_id")
        if not record_id:
            raise ValueError("Missing 'record_id'")
            
        success = manager.mock_client.delete_record(record_id)
        return {"success": success}

    elif method == "rename_record":
        if not manager.mock_client:
            raise ValueError("Mock client not available")
        
        record_id = params.get("record_id")
        alias = params.get("alias")
        if not record_id or alias is None:
            raise ValueError("Missing 'record_id' or 'alias'")
            
        success = manager.mock_client.rename_record(record_id, alias)
        return {"success": success}

    else:
        raise ValueError(f"Unknown method: {method}")


def create_response(request_id: Any, result: Any = None, error: Optional[Dict] = None) -> str:
    """Create a JSON-RPC 2.0 response."""
    response: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    return json.dumps(response)


def create_error(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a JSON-RPC error object."""
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return error


def main() -> None:
    """Main server loop."""
    # Send ready signal
    print(json.dumps({"jsonrpc": "2.0", "method": "$/ready", "params": {"status": "ok"}}), flush=True)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                print(create_response(None, error=create_error(-32700, "Parse error", str(e))), flush=True)
                continue
            
            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params")
            
            if not method:
                print(create_response(request_id, error=create_error(-32600, "Invalid Request", "Missing 'method'")), flush=True)
                continue
            
            try:
                result = handle_request(method, params)
                print(create_response(request_id, result=result), flush=True)
            except ValueError as e:
                # Method not found or missing parameter
                log_stderr(f"ValueError: {e}")
                print(create_response(request_id, error=create_error(-32601, "Method not found", str(e))), flush=True)
            except Exception as e:
                log_stderr(f"Error: {e}")
                print(create_response(request_id, error=create_error(-32603, "Internal error", str(e))), flush=True)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log_stderr(f"Unexpected: {e}")
            continue


if __name__ == "__main__":
    main()
