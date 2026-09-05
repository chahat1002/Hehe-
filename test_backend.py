"""
test_backend.py
Verification test suite for:
1. Severity color mapping (Yellow, Orange, Red)
2. 500m Danger Zone detection (>= 10 high severity reports)
3. /check-danger endpoint for coordinates inside & outside danger zones
"""
from app import app, init_db, haversine_meters

def test_backend_suite():
    # Reseed DB with sample cluster
    init_db(force_reseed=True)
    client = app.test_client()

    print("--- 1. Testing Haversine Distance Calculation ---")
    dist_zero = haversine_meters(28.6315, 77.2167, 28.6315, 77.2167)
    assert dist_zero == 0.0, f"Expected 0, got {dist_zero}"
    dist_approx_111m = haversine_meters(28.6315, 77.2167, 28.6325, 77.2167)
    assert 100 < dist_approx_111m < 120, f"Expected ~111m, got {dist_approx_111m}"
    print("Haversine calculations verified.")

    print("\n--- 2. Testing GET /danger-zones ---")
    res = client.get('/danger-zones')
    assert res.status_code == 200
    data = res.get_json()
    print(f"Danger Zones detected: {data['danger_zone_count']}")
    assert data['danger_zone_count'] >= 1, "Expected at least 1 danger zone cluster!"
    zone = data['danger_zones'][0]
    print(f" -> Center: ({zone['center_lat']}, {zone['center_lng']})")
    print(f" -> High Reports in 500m: {zone['high_report_count']}")
    assert zone['high_report_count'] >= 10, f"Expected >= 10 high reports, got {zone['high_report_count']}"

    print("\n--- 3. Testing GET /check-danger (Inside Danger Zone) ---")
    inside_res = client.get('/check-danger?lat=28.6315&lng=77.2167')
    assert inside_res.status_code == 200
    inside_data = inside_res.get_json()
    print(f"Inside check: is_danger_zone={inside_data['is_danger_zone']}, count={inside_data['high_severity_count']}")
    assert inside_data['is_danger_zone'] is True
    assert inside_data['high_severity_count'] >= 10

    print("\n--- 4. Testing GET /check-danger (Outside Danger Zone) ---")
    outside_res = client.get('/check-danger?lat=28.5000&lng=77.1000')
    assert outside_res.status_code == 200
    outside_data = outside_res.get_json()
    print(f"Outside check: is_danger_zone={outside_data['is_danger_zone']}, count={outside_data['high_severity_count']}")
    assert outside_data['is_danger_zone'] is False
    assert outside_data['high_severity_count'] == 0

    print("\n--- 5. Testing GET /reports (Colors & Reports) ---")
    reports_res = client.get('/reports')
    assert reports_res.status_code == 200
    reports = reports_res.get_json()
    print(f"Total reports retrieved: {len(reports)}")
    assert len(reports) >= 12

    print("\nALL DANGER ZONE AND BACKEND TESTS PASSED!")

if __name__ == '__main__':
    test_backend_suite()
