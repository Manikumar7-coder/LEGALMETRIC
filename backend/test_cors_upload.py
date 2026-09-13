import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_cors(origin):
    print(f"\n--- Testing CORS from Origin: {origin} ---")
    
    # 1. Test OPTIONS preflight on /api/inspections/analyze
    preflight_headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    r_options = requests.options(f"{BASE_URL}/api/inspections/analyze", headers=preflight_headers)
    print("Preflight Status:", r_options.status_code)
    print("Allow-Origin:", r_options.headers.get("access-control-allow-origin"))
    print("Allow-Credentials:", r_options.headers.get("access-control-allow-credentials"))
    print("Allow-Headers:", r_options.headers.get("access-control-allow-headers"))
    print("Allow-Methods:", r_options.headers.get("access-control-allow-methods"))
    assert r_options.status_code == 200
    assert r_options.headers.get("access-control-allow-origin") == origin
    assert r_options.headers.get("access-control-allow-credentials") == "true"

    # 2. Login
    r_login = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "officer@safemetric.gov.in", "password": "password123"},
        headers={"Origin": origin}
    )
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    print("Login successful, token obtained.")

    # 3. Test analyze endpoint (end-to-end inspection pipeline)
    with open("demo_samples/sample_saferice.png", "rb") as f:
        files = {"file": ("sample_saferice.png", f, "image/png")}
        data = {
            "product_name": "SafeRice",
            "package_length_mm": "150",
            "package_width_mm": "200"
        }
        headers = {
            "Origin": origin,
            "Authorization": f"Bearer {token}",
        }
        r_analyze = requests.post(f"{BASE_URL}/api/inspections/analyze", files=files, data=data, headers=headers)
        print("Analyze Status:", r_analyze.status_code)
        print("Analyze Allow-Origin:", r_analyze.headers.get("access-control-allow-origin"))
        print("Analyze Allow-Credentials:", r_analyze.headers.get("access-control-allow-credentials"))
        assert r_analyze.status_code == 200
        res_data = r_analyze.json()
        print("Analyze Success! Inspection ID:", res_data.get("id"))
        print("Overall Status:", res_data.get("overall_status"))
        print("Compliance Score:", res_data.get("compliance_score"))
        assert res_data.get("id") is not None
        return True

if __name__ == "__main__":
    for orig in [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ]:
        test_cors(orig)
    print("\n======================================================================")
    print(" ALL CORS & INSPECTION ANALYZE TESTS PASSED SUCCESSFULLY (100%)!")
    print("======================================================================")
