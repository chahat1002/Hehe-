import sqlite3
import os
import math
import webbrowser
import folium

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports.db')
OUTPUT_MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marked_map.html')

SEVERITY_COLORS = {
    'Low':    {'color': '#eab308', 'name': 'Yellow', 'label': 'Very Minor Inconvenience'},
    'Medium': {'color': '#f97316', 'name': 'Orange', 'label': 'Normal Issue'},
    'High':   {'color': '#ef4444', 'name': 'Red',    'label': 'Extreme Issue'}
}

def resolve_severity(severity_str):
    s = (severity_str or '').strip().lower()
    if any(k in s for k in ['extreme', 'high', 'severe', 'red']):
        return 'High', SEVERITY_COLORS['High']
    elif any(k in s for k in ['normal', 'medium', 'orange']):
        return 'Medium', SEVERITY_COLORS['Medium']
    return 'Low', SEVERITY_COLORS['Low']

def haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def detect_danger_zones(reports, radius_meters=500, min_high_reports=10):
    high_reports = [r for r in reports if r['severity'] == 'High']
    if len(high_reports) < min_high_reports:
        return []

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
                if current_cluster_ids & other_ids:
                    used_indices.add(j)
                    current_cluster_ids.update(other_ids)
                    for r in other:
                        if r['id'] not in {x['id'] for x in current_reports}:
                            current_reports.append(r)

        center_lat = sum(r['lat'] for r in current_reports) / len(current_reports)
        center_lng = sum(r['lng'] for r in current_reports) / len(current_reports)
        merged_zones.append({
            'center_lat': center_lat,
            'center_lng': center_lng,
            'radius_meters': radius_meters,
            'count': len(current_reports)
        })
    return merged_zones

def generate_interactive_map(open_browser=True):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports ORDER BY id DESC')
    reports = cursor.fetchall()
    conn.close()

    if not reports:
        print("No reports found in database.")
        return

    report_dicts = []
    for r in reports:
        canonical_sev, meta = resolve_severity(r['severity'])
        report_dicts.append({
            'id': r['id'],
            'lat': float(r['lat']),
            'lng': float(r['lng']),
            'severity': canonical_sev,
            'color': meta['color'],
            'name': meta['name'],
            'label': meta['label'],
            'category': r['category'] or 'Incident',
            'description': r['description'] or '',
            'timestamp': r['timestamp'] or 'N/A'
        })

    avg_lat = sum(r['lat'] for r in report_dicts) / len(report_dicts)
    avg_lng = sum(r['lng'] for r in report_dicts) / len(report_dicts)

    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=14, tiles='CartoDB dark_matter')

    # Detect & Draw 500m Danger Zones (>= 10 high-severity reports)
    danger_zones = detect_danger_zones(report_dicts, radius_meters=500, min_high_reports=10)
    for dz in danger_zones:
        # Draw 500m red danger perimeter
        folium.Circle(
            location=[dz['center_lat'], dz['center_lng']],
            radius=dz['radius_meters'],
            color='#ef4444',
            weight=3,
            fill=True,
            fill_color='#ef4444',
            fill_opacity=0.22,
            popup=f"<b>🚨 DANGER ZONE</b><br>{dz['count']} High Severity Reports within 500m perimeter.<br>Extreme caution advised!"
        ).add_to(m)

        # Danger zone center badge
        folium.Marker(
            location=[dz['center_lat'], dz['center_lng']],
            icon=folium.DivIcon(
                html=f"""
                <div style="background: rgba(239, 68, 68, 0.9); color: white; border: 2px solid white; border-radius: 12px; padding: 3px 8px; font-weight: bold; font-size: 11px; white-space: nowrap; box-shadow: 0 0 12px red;">
                    ⚠️ DANGER ZONE ({dz['count']} High Reports)
                </div>
                """
            )
        ).add_to(m)

    # Plot individual reports
    for r in report_dicts:
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 200px;">
            <b style="color: {r['color']}; font-size: 14px;">● {r['label']} ({r['name']})</b>
            <p><b>Category:</b> {r['category']}</p>
            <p><i>"{r['description']}"</i></p>
            <small style="color: #64748b;">Logged at {r['timestamp']} | ({r['lat']:.4f}, {r['lng']:.4f})</small>
        </div>
        """

        folium.CircleMarker(
            location=[r['lat'], r['lng']],
            radius=10,
            color='#ffffff',
            weight=2,
            fill=True,
            fill_color=r['color'],
            fill_opacity=0.92,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{r['name']} Pin ({r['severity']})"
        ).add_to(m)

    m.save(OUTPUT_MAP_FILE)
    print(f"[Success] Generated map with {len(danger_zones)} Danger Zones and {len(report_dicts)} colored pins: {OUTPUT_MAP_FILE}")

    if open_browser:
        webbrowser.open(f"file:///{os.path.abspath(OUTPUT_MAP_FILE)}")

if __name__ == '__main__':
    generate_interactive_map(open_browser=False)
