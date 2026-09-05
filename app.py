import sqlite3
import os
import math
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports.db')

# =============================================================
# Severity Color Palette:
# - Yellow: Very minor inconvenience (Low)
# - Orange: Normal issue (Medium)
# - Red: Extreme issue (High)
# =============================================================
SEVERITY_COLORS = {
    'Low': {
        'hex': '#eab308',
        'color_name': 'yellow',
        'label': 'Very Minor Inconvenience (Low)'
    },
    'Medium': {
        'hex': '#f97316',
        'color_name': 'orange',
        'label': 'Normal Issue (Medium)'
    },
    'High': {
        'hex': '#ef4444',
        'color_name': 'red',
        'label': 'Extreme Issue (High)'
    }
}

def resolve_severity_color(severity_input: str):
    """
    Normalizes severity inputs to standard values and returns corresponding color metadata:
      - Yellow (#eab308) for minor inconvenience
      - Orange (#f97316) for normal issue
      - Red (#ef4444) for extreme issue
    """
    s = (severity_input or '').strip().lower()
    if any(k in s for k in ['extreme', 'high', 'severe', 'red']):
        return 'High', SEVERITY_COLORS['High']
    elif any(k in s for k in ['normal', 'medium', 'orange']):
        return 'Medium', SEVERITY_COLORS['Medium']
    else:
        return 'Low', SEVERITY_COLORS['Low']

def haversine_meters(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two GPS points in meters
    using the Haversine formula.
    """
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def detect_danger_zones(reports, radius_meters=500, min_high_reports=10):
    """
    Finds clusters of high-severity reports where >= min_high_reports exist
    within radius_meters (500m).
    Groups overlapping clusters so danger zones are cleanly rendered.
    """
    high_reports = [r for r in reports if r.get('severity') == 'High']
    if len(high_reports) < min_high_reports:
        return []

    # Find neighbor clusters for each high-severity point
    clusters = []
    for r in high_reports:
        neighbors = [
            n for n in high_reports
            if haversine_meters(r['lat'], r['lng'], n['lat'], n['lng']) <= radius_meters
        ]
        if len(neighbors) >= min_high_reports:
            clusters.append(neighbors)

    if not clusters:
        return []

    # Merge overlapping clusters (connected components)
    merged_zones = []
    used_indices = set()

    for i, cluster in enumerate(clusters):
        if i in used_indices:
            continue
        current_cluster_ids = {r['id'] for r in cluster}
        current_reports = list(cluster)
        used_indices.add(i)

        for j, other in enumerate(clusters):
            if j not in used_indices:
                other_ids = {r['id'] for r in other}
                if current_cluster_ids & other_ids:  # overlap found
                    used_indices.add(j)
                    current_cluster_ids.update(other_ids)
                    for r in other:
                        if r['id'] not in {x['id'] for x in current_reports}:
                            current_reports.append(r)

        # Calculate geometric center of the danger zone
        center_lat = sum(r['lat'] for r in current_reports) / len(current_reports)
        center_lng = sum(r['lng'] for r in current_reports) / len(current_reports)

        merged_zones.append({
            'zone_id': len(merged_zones) + 1,
            'center_lat': round(center_lat, 6),
            'center_lng': round(center_lng, 6),
            'radius_meters': radius_meters,
            'high_report_count': len(current_reports),
            'threshold': min_high_reports,
            'title': f"Danger Zone ({len(current_reports)} High Severity Reports)",
            'report_ids': list(current_cluster_ids)
        })

    return merged_zones

def get_db_connection():
    """Establishes connection to SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reseed=False):
    """
    Initializes the reports table if it doesn't exist and seeds data.
    Seeds a cluster of 10 high-severity reports within 500m in Connaught Place
    so the Danger Zone is instantly active and demonstrable.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            severity TEXT NOT NULL,
            category TEXT,
            description TEXT,
            timestamp TEXT
        )
    ''')

    if force_reseed:
        cursor.execute('DELETE FROM reports')

    cursor.execute('SELECT COUNT(*) FROM reports')
    count = cursor.fetchone()[0]

    if count < 10 or force_reseed:
        # A cluster of 10 high-severity reports located within ~250m of (28.6315, 77.2167)
        danger_zone_cluster = [
            (28.6315, 77.2167, 'High', 'Assault,Harassment', 'Multiple harassment reports near inner circle alleyway late at night.', '11:15 PM'),
            (28.6320, 77.2170, 'High', 'Assault,No CCTV', 'Physical assault and robbery reported near dark walkway.', '10:45 PM'),
            (28.6310, 77.2162, 'High', 'Harassment,Poor lighting', 'Severe catcalling and following reported by multiple women.', '09:50 PM'),
            (28.6325, 77.2165, 'High', 'Harassment,Isolated area', 'Isolated subway passage with zero security guards.', '10:10 PM'),
            (28.6312, 77.2173, 'High', 'Assault', 'Late night harassment near bus stop.', '11:30 PM'),
            (28.6308, 77.2168, 'High', 'No CCTV,Harassment', 'Aggressive stalker incident reported.', '10:05 PM'),
            (28.6322, 77.2160, 'High', 'Assault,Poor lighting', 'Broken streetlight area with repeated muggings.', '08:45 PM'),
            (28.6317, 77.2175, 'High', 'Harassment', 'Group harassment incident outside closed shops.', '11:00 PM'),
            (28.6305, 77.2164, 'High', 'Assault,Harassment', 'Threatening behavior and stalking incident.', '09:30 PM'),
            (28.6328, 77.2172, 'High', 'Harassment,No CCTV', 'Unsafe junction after 9 PM, no police presence.', '10:20 PM'),
            # Spread out medium and low reports
            (28.6250, 77.2150, 'Medium', 'Poor lighting,Isolated area', 'Street lights malfunctioning on this stretch for over a week.', '09:15 PM'),
            (28.6020, 77.2250, 'Low', 'Accident-prone', 'Narrow intersection with high traffic during rush hours.', '07:30 PM')
        ]
        cursor.executemany('''
            INSERT INTO reports (lat, lng, severity, category, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', danger_zone_cluster)
        conn.commit()
        print(f"[DB] Seeded database with {len(danger_zone_cluster)} reports including a 500m Danger Zone cluster.")

    conn.close()

# -------------------------------------------------------------
# 1. Root Route: Serves index.html
# -------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({
        "status": "online",
        "message": "SafeRoute Backend API is running!",
        "endpoints": {
            "GET /reports": "Retrieve all safety reports with assigned colors",
            "POST /reports": "Submit a new safety report",
            "GET /danger-zones": "Retrieve 500m Danger Zones (>= 10 high-severity reports)",
            "GET /check-danger?lat=...&lng=...": "Check if a specific coordinate is in a danger zone"
        }
    })

# -------------------------------------------------------------
# 2. GET /reports: Reads from DB and assigns colors
# -------------------------------------------------------------
@app.route('/reports', methods=['GET'])
def get_reports():
    """
    Fetches all reports from reports.db and attaches the exact color:
      - Yellow (#eab308)
      - Orange (#f97316)
      - Red (#ef4444)
    Also computes and returns active Danger Zones.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports ORDER BY id DESC')
    rows = cursor.fetchall()

    reports_list = []
    for row in rows:
        raw_category = row['category'] or ''
        categories = [c.strip() for c in raw_category.split(',') if c.strip()]
        canonical_sev, color_meta = resolve_severity_color(row['severity'])

        reports_list.append({
            'id': row['id'],
            'lat': float(row['lat']),
            'lng': float(row['lng']),
            'severity': canonical_sev,
            'color': color_meta['hex'],
            'color_name': color_meta['color_name'],
            'severity_label': color_meta['label'],
            'category': raw_category,
            'categories': categories,
            'description': row['description'] or '',
            'timestamp': row['timestamp'] or ''
        })
    conn.close()

    # Detect danger zones (>= 10 high-severity reports within 500m)
    danger_zones = detect_danger_zones(reports_list, radius_meters=500, min_high_reports=10)

    # If client specifically asks for full payload wrapper
    if request.args.get('format') == 'extended':
        return jsonify({
            'reports': reports_list,
            'danger_zones': danger_zones
        }), 200

    # Default: Return reports list with header or metadata
    response = jsonify(reports_list)
    response.headers['X-Danger-Zones-Count'] = str(len(danger_zones))
    return response, 200

# -------------------------------------------------------------
# 3. GET /danger-zones: Returns all active 500m Danger Zones
# -------------------------------------------------------------
@app.route('/danger-zones', methods=['GET'])
def get_danger_zones():
    """
    Returns all detected Danger Zones across the entire database.
    A Danger Zone is defined as an area with >= 10 high-severity reports within 500m.
    """
    radius = float(request.args.get('radius', 500))
    threshold = int(request.args.get('threshold', 10))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE severity = 'High'")
    rows = cursor.fetchall()
    conn.close()

    high_reports = [
        {
            'id': r['id'],
            'lat': float(r['lat']),
            'lng': float(r['lng']),
            'severity': 'High',
            'category': r['category'],
            'description': r['description']
        }
        for r in rows
    ]

    zones = detect_danger_zones(high_reports, radius_meters=radius, min_high_reports=threshold)

    return jsonify({
        'radius_meters': radius,
        'threshold': threshold,
        'danger_zone_count': len(zones),
        'danger_zones': zones
    }), 200

# -------------------------------------------------------------
# 4. GET /check-danger: Check if a specific (lat, lng) is in a Danger Zone
# -------------------------------------------------------------
@app.route('/check-danger', methods=['GET'])
def check_danger():
    """
    Checks if a given coordinate (lat, lng) has >= 10 high-severity reports
    within 500 meters.
    """
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid 'lat' and 'lng' query parameters are required."}), 400

    radius = float(request.args.get('radius', 500))
    threshold = int(request.args.get('threshold', 10))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE severity = 'High'")
    high_rows = cursor.fetchall()
    conn.close()

    nearby_high = []
    for row in high_rows:
        dist = haversine_meters(lat, lng, float(row['lat']), float(row['lng']))
        if dist <= radius:
            nearby_high.append({
                'id': row['id'],
                'lat': float(row['lat']),
                'lng': float(row['lng']),
                'distance_meters': round(dist, 1),
                'category': row['category'],
                'description': row['description'],
                'timestamp': row['timestamp']
            })

    count = len(nearby_high)
    is_danger = count >= threshold

    return jsonify({
        'lat': lat,
        'lng': lng,
        'radius_meters': radius,
        'threshold': threshold,
        'high_severity_count': count,
        'is_danger_zone': is_danger,
        'status': 'DANGER_ZONE' if is_danger else ('WARNING' if count >= 5 else 'NORMAL'),
        'nearby_high_reports': nearby_high
    }), 200

# -------------------------------------------------------------
# 5. POST /reports: Inserts new report into SQLite
# -------------------------------------------------------------
@app.route('/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    lat = data.get('lat')
    lng = data.get('lng')
    severity = data.get('severity')
    description = data.get('description', '')

    if lat is None or lng is None or not severity:
        return jsonify({"error": "Fields 'lat', 'lng', and 'severity' are required."}), 400

    canonical_sev, color_meta = resolve_severity_color(severity)
    categories_raw = data.get('categories') or data.get('category') or []
    if isinstance(categories_raw, list):
        category_str = ",".join(str(c).strip() for c in categories_raw if str(c).strip())
    else:
        category_str = str(categories_raw).strip()

    timestamp = data.get('timestamp') or datetime.now().strftime("%I:%M %p")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (lat, lng, severity, category, description, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (lat, lng, canonical_sev, category_str, description, timestamp))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Report created successfully",
        "report": {
            'id': new_id,
            'lat': float(lat),
            'lng': float(lng),
            'severity': canonical_sev,
            'color': color_meta['hex'],
            'color_name': color_meta['color_name'],
            'severity_label': color_meta['label'],
            'categories': [c.strip() for c in category_str.split(',') if c.strip()],
            'category': category_str,
            'description': description,
            'timestamp': timestamp
        }
    }), 201

if __name__ == '__main__':
    import socket
    init_db()

    # Detect local Wi-Fi / LAN IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = '127.0.0.1'

    print("=" * 60)
    print(" SafeRoute Backend is LIVE!")
    print(f" -> For YOUR laptop:    http://127.0.0.1:5000")
    print(f" -> For OTHER laptops:  http://{local_ip}:5000")
    print("    (Note: Other laptops must be on the SAME Wi-Fi network)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
