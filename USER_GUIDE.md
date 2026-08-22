# SafeRoute — User & Developer Guide

**SafeRoute** is an interactive, web-based community safety and incident reporting map for Delhi, India. Built with a single-file architecture using **Leaflet.js** and **OpenStreetMap**, it allows users to visually log, explore, and track safety reports in real time.

---

## 🌟 Key Features

1. **Interactive Delhi Map**
   - Centered at **Delhi, India** (`28.6139° N, 77.2090° E`) at zoom level `13`.
   - Smooth panning, zooming, and interactive custom map popups.

2. **Map Click-to-Report Workflow**
   - Click anywhere on the map to drop a temporary selection pin.
   - Automatically opens the **Safety Report Form** in the sidebar with target coordinates.

3. **Color-Coded Severity Legend Badges**
   - Dynamic top header badges featuring live incident counts:
     - 🔴 **High Severity** (Red): Critical incidents (e.g., assault, physical danger).
     - 🟠 **Medium Severity** (Orange): Moderately unsafe conditions (e.g., poor lighting, isolated paths, no CCTV).
     - 🟢 **Low Severity** (Green): Minor hazards (e.g., traffic bottleneck, accident-prone spot).

4. **Detailed Incident Categorization**
   - Multi-select category checkboxes:
     - Assault / Physical incident
     - Harassment / Catcalling
     - Poor lighting
     - No CCTV coverage
     - Isolated area
     - Accident-prone spot
   - Optional text description for extra context.

5. **Live Sidebar Reports Feed**
   - All submitted reports are saved in memory and displayed in the sidebar list.
   - Automatically sorted **most recent first**.
   - Displays real-time report count badges.

6. **Responsive Mobile & Desktop Design**
   - **Desktop**: Split screen with map on left, sidebar form & feed on right.
   - **Mobile**: Vertical stacked layout (interactive map top ~52vh, scrollable feed bottom ~48vh).

---

## 🚀 How to Use the Application

### 1. Launching the App
Simply open `index.html` in any standard web browser (Chrome, Firefox, Edge, Safari). No npm server or build step required.

```bash
# Double-click index.html or open via terminal
start d:\college work\vibe coding\safe_route_app\index.html
```

---

### 2. Exploring Reports
- **Map Pins**: Click on any colored pin on the map to open a popup detailing the severity, category, description, and exact coordinates.
- **Sidebar Feed**: Scroll down the right sidebar to browse recent incident cards.
- **Header Legend**: Observe the live badge count in the header showing total High, Medium, and Low severity reports.

---

### 3. Submitting a New Safety Report

```
[ Click Map Location ] ➔ [ Temporary Pin Appears ] ➔ [ Sidebar Form Opens ]
                                                              │
                                                              ▼
[ Permanent Marker Rendered ] ◄─ [ In-Memory Array Updated ] ◄─ [ Fill Form & Submit ]
```

1. **Click Map Location**: Click on any road, landmark, or intersection on the map.
2. **Review Target Pin**: A blue temporary marker pin will highlight the selected location, and the form will open in the sidebar showing the exact latitude and longitude.
3. **Select Severity**: Choose `🔴 High`, `🟠 Medium`, or `🟢 Low` severity.
4. **Choose Categories**: Check one or more relevant category boxes (e.g., *Poor lighting*, *No CCTV*).
5. **Add Optional Description**: Type any helpful notes or details for community members.
6. **Click "Submit Report"**:
   - The temporary marker converts into a permanent color-coded map pin.
   - The report is added to the in-memory JavaScript dataset.
   - The sidebar list updates immediately with your new report card at the top.
   - Legend badge counts increment automatically.

---

## 🛠️ Technical Stack & Architecture

- **Core**: HTML5, CSS3, JavaScript (ES6+).
- **Mapping Library**: [Leaflet.js v1.9.4](https://leafletjs.com/) (CDN-hosted).
- **Tile Layer**: [OpenStreetMap](https://www.openstreetmap.org/) standard tiles.
- **Typography**: [Google Fonts — Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans).
- **Data Model**: In-memory JavaScript array (`reports`) storing report objects:

```javascript
{
  id: 1771700000000,
  lat: 28.6139,
  lng: 77.2090,
  severity: "High", // "High" | "Medium" | "Low"
  categories: ["Assault", "No CCTV"],
  description: "Reported incident description",
  timestamp: "10:45 PM"
}
```

---

## 📌 File Directory

```
safe_route_app/
├── index.html        # Single-file HTML/CSS/JS interactive map application
└── USER_GUIDE.md     # Application User & Developer Guide
```
