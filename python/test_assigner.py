"""Test assigner integration with complex_example."""
import json
import subprocess
import os
import sys

def test_assigner():
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
        print(f"Ready signal: {ready.strip()}")

        # 2. Load complex_example project
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "complex_example", "complex_1"))
        res = send_request("load_project", {"path": project_dir})
        print(f"Load project result: {res['result']}")

        # 3. Get variables to confirm model loaded
        res = send_request("get_variables")
        print(f"Variables loaded: {len(res['result'])} fields")

        # 4. Test calculate with sample data
        sample_data = {
            "blank_qr_mean": 0.05,
            "control_qr_mean": 1.25,
            "quantum_measurements": [
                {"well_position": "A1", "quantum_resonance": 0.35, "group_type": "处理组", "energy_level": 100.0},
                {"well_position": "A2", "quantum_resonance": 0.55, "group_type": "处理组", "energy_level": 50.0},
                {"well_position": "A3", "quantum_resonance": 0.85, "group_type": "处理组", "energy_level": 25.0},
                {"well_position": "A4", "quantum_resonance": 1.05, "group_type": "处理组", "energy_level": 10.0},
            ],
            "stability_field": 99.5,
            "culture_temp": 37.0,
            "adhesion_time": 24.0,
            "treatment_duration": 48.0,
            "cck8_incubation_time": 2.0,
        }
        
        res = send_request("calculate", {"data": sample_data})
        result = res.get('result', {})
        
        print("\n=== Calculation Results ===")
        calculated_fields = result.get('calculated_fields', {})
        
        if 'inhibition_results' in calculated_fields:
            print("\n📊 Inhibition Results:")
            for r in calculated_fields['inhibition_results']:
                print(f"  Energy {r['energy_level']} TeV -> {r['inhibition_rate']:.1f}% ({r['confidence_level']})")
        
        if 'dimension_stability_check' in calculated_fields:
            check = calculated_fields['dimension_stability_check']
            print(f"\n✅ Dimension Stability: {'✓' if check['checked'] else '✗'} {check.get('annotation', '')}")
        
        if 'temperature_check' in calculated_fields:
            check = calculated_fields['temperature_check']
            print(f"✅ Temperature Check: {'✓' if check['checked'] else '✗'} {check.get('annotation', '')}")
        
        if 'estimated_total_time' in calculated_fields:
            time_info = calculated_fields['estimated_total_time']
            print(f"\n⏱️ Estimated Time: {time_info['hours']} hours")

        # Shutdown
        send_request("shutdown")
        process.wait(timeout=2)
        print("\nBackend shut down successfully")

    finally:
        # Print stderr for debugging
        stderr = process.stderr.read()
        if stderr:
            print("\n--- Backend Logs ---")
            print(stderr)
        
        if process.poll() is None:
            process.terminate()

if __name__ == "__main__":
    test_assigner()
