import json
import subprocess
import os
import sys
import tempfile

def test_integration():
    print("Starting Integration Test...")
    
    # Start the backend process
    backend_path = os.path.join(os.path.dirname(__file__), "server.py")
    process = subprocess.Popen(
        [sys.executable, backend_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def send_request(method, params=None):
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            return None
        return json.loads(line)

    try:
        # 1. Wait for ready signal
        ready = process.stdout.readline()
        print(f"Backend Ready: {ready.strip()}")

        # 2. Load Project (Use simple_example or temp dir)
        # For safety, let's create a temp directory with a dummy model.py
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Created temp project at: {temp_dir}")
            
            # Create dummy model.py
            model_content = """
from pydantic import BaseModel, Field
from airalogy.types import FileIdPNG
from typing import Optional

class VarModel(BaseModel):
    test_file: Optional[FileIdPNG] = Field(default=None, title="Test File")
    demo_var: str = Field(default="initial", title="Demo Var")
"""
            # Create airalogy/types.py mock if needed? 
            # The backend server tries to import airalogy. 
            # If airalogy is installed in the environment, it works. 
            # If not, the server sets HAS_AIRALOGY = False.
            # But our dummy model imports it. 
            # Let's hope the environment has it, or we mock it in the model file itself if needed.
            # Actually, let's just use string types if we are not sure about environment.
            # But the user specifically mentioned FileIdPNG.
            # Let's try to use the existing 'simple_example' if verify_backend.py used it.
            
            project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "simple_example", "protocol_v5"))
            if not os.path.exists(project_dir):
                print(f"Warning: {project_dir} not found. Using temp dir with minimal model.")
                # We need to ensure importable types if using temp dir.
                # Simplest is just basic types to test variable update.
                with open(os.path.join(temp_dir, "model.py"), "w") as f:
                    f.write("from pydantic import BaseModel, Field\nclass VarModel(BaseModel):\n    my_var: str = 'default'\n")
                project_dir = temp_dir
            
            res = send_request("load_project", {"path": project_dir})
            print(f"Load Project: {res}")
            if not res or not res.get("result", {}).get("success"):
                print("Failed to load project. Check stderr.")
                # Read stderr non-blocking? Hard in this simple script.
                # Just continue and see.

            # 3. Test File Upload
            # Create a dummy file
            dummy_file_path = os.path.join(temp_dir, "test_upload.png")
            with open(dummy_file_path, "wb") as f:
                f.write(b"fake image content")
            
            res = send_request("file:upload", {"filePath": dummy_file_path})
            print(f"File Upload: {res}")
            file_id = res["result"]["id"]
            print(f"Got File ID: {file_id}")

            # 4. Test Variable Update (Sync)
            # Pick a variable. If using simple_example, maybe 'incubator_settings_photo' or 'mission_code'?
            # Let's assume 'incubator_settings_photo' exists based on user screenshots.
            target_var = "incubator_settings_photo"
            
            # Check initial value
            res = send_request("get_variables")
            vars_meta = res["result"]
            # If target_var not in vars, pick first one
            if target_var not in vars_meta:
                target_var = list(vars_meta.keys())[0]
            
            print(f"Target Var: {target_var}, Initial Default: {vars_meta[target_var].get('default_value')}")

            # Update it with the new file ID
            res = send_request("variable:update", {"fieldName": target_var, "value": file_id})
            print(f"Variable Update: {res}")

            # 5. Verify Update Persists in Metadata
            res = send_request("get_variables")
            new_vars_meta = res["result"]
            new_default = new_vars_meta[target_var].get("default_value")
            print(f"Target Var: {target_var}, New Default: {new_default}")
            
            if new_default == file_id:
                print("✅ SUCCESS: Variable update verified!")
            else:
                print("❌ FAILURE: Variable did not update.")

    except Exception as e:
        print(f"Test Error: {e}")
        # Print stderr if possible
        # print("Server Stderr:", process.stderr.read()) 
    finally:
        send_request("shutdown")
        process.wait(timeout=2)

if __name__ == "__main__":
    test_integration()
