import math
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- IN-MEMORY DATABASE ---
# Stores all submitted raw reports
reports_db = []

# Threshold for confirming a dangerous location
CONFIRMATION_THRESHOLD = 5
RADIUS_METERS = 100.0  # Reports within 100 meters are grouped together


# --- BLOCK 1: Distance Calculation Helper (Haversine Formula) ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two GPS points in meters
    using the Haversine formula.
    """
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in meters


# --- BLOCK 2: API Health Check ---
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend status."""
    return jsonify({
        "status": "online",
        "total_reports": len(reports_db)
    }), 200


# --- BLOCK 3: Endpoint 1 - Submit New Unsafe Location Report (POST) ---
@app.route("/api/reports", methods=["POST"])
def submit_report():
    """
    Accepts a new unsafe location report from a user.
    Expects JSON body: { "latitude": float, "longitude": float, "description": str }
    """
    data = request.get_json()

    # Validation: Check required fields
    if not data or "latitude" not in data or "longitude" not in data:
        return jsonify({
            "success": False,
            "error": "Missing required fields: 'latitude' and 'longitude' are mandatory"
        }), 400

    try:
        lat = float(data["latitude"])
        lon = float(data["longitude"])
    except ValueError:
        return jsonify({"success": False, "error": "'latitude' and 'longitude' must be valid numbers"}), 400

    # Build the report object with server-generated timestamp
    new_report = {
        "id": len(reports_db) + 1,
        "latitude": lat,
        "longitude": lon,
        "description": data.get("description", "Unspecified safety concern"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    reports_db.append(new_report)

    return jsonify({
        "success": True,
        "message": "Report submitted successfully",
        "report": new_report
    }), 201


# --- BLOCK 4: Endpoint 2 - Return Clustered & Confirmed Locations (GET) ---
@app.route("/api/reports", methods=["GET"])
def get_clustered_reports():
    """
    Groups reports within ~100 meters of each other.
    Marks a location cluster as 'confirmed' if count >= 5.
    """
    clusters = []

    for report in reports_db:
        r_lat = report["latitude"]
        r_lon = report["longitude"]
        assigned = False

        # Try to find an existing cluster within 100 meters
        for cluster in clusters:
            dist = haversine_distance(r_lat, r_lon, cluster["center_latitude"], cluster["center_longitude"])
            if dist <= RADIUS_METERS:
                cluster["reports"].append(report)
                cluster["count"] += 1
                cluster["descriptions"].append(report["description"])
                # Update cluster center average
                cluster["center_latitude"] = sum(r["latitude"] for r in cluster["reports"]) / cluster["count"]
                cluster["center_longitude"] = sum(r["longitude"] for r in cluster["reports"]) / cluster["count"]
                cluster["is_confirmed"] = cluster["count"] >= CONFIRMATION_THRESHOLD
                assigned = True
                break

        # If report is not near any existing cluster, create a new cluster
        if not assigned:
            clusters.append({
                "cluster_id": len(clusters) + 1,
                "center_latitude": r_lat,
                "center_longitude": r_lon,
                "count": 1,
                "is_confirmed": 1 >= CONFIRMATION_THRESHOLD,  # False initially
                "descriptions": [report["description"]],
                "reports": [report]
            })

    return jsonify({
        "success": True,
        "total_clusters": len(clusters),
        "data": clusters
    }), 200


# --- BLOCK 5: Server Entry Point ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)



