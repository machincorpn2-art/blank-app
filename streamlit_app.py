import math
import streamlit as st


# ============================================================================
# AUTHENTICATION STATE ENGINE
# ============================================================================
def _init_auth_state():
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "is_premium" not in st.session_state:
        st.session_state.is_premium = True
    if "selected_component" not in st.session_state:
        st.session_state.selected_component = "Flange"


def _authenticate_user(username, password):
    """Offline authentication engine."""
    if username and password and len(username) >= 3 and len(password) >= 4:
        st.session_state.auth_user = username
        return True
    return False


def _logout_user():
    st.session_state.auth_user = None


# ============================================================================
# GEOMETRIC VALIDATION
# ============================================================================
def _validate_flange(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height):
    errors = []
    if outer_dia <= inner_dia:
        errors.append("Outer diameter must be greater than bore diameter")
    if hub_dia >= outer_dia - 30:
        errors.append("Hub diameter too large for outer diameter")
    if hub_dia <= inner_dia:
        errors.append("Hub diameter must be larger than bore diameter")
    if bolt_count < 4:
        errors.append("Flange requires at least four bolts")
    if bolt_dia <= 0:
        errors.append("Bolt diameter must be positive")
    return errors


def _validate_shaft(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth):
    errors = []
    if dia2 >= dia1:
        errors.append("Section 2 diameter must be smaller than Section 1")
    if key_len >= len1:
        errors.append("Keyway length must be less than Section 1 length")
    if key_width >= dia1:
        errors.append("Keyway width exceeds shaft diameter")
    if key_depth >= dia1 / 2:
        errors.append("Keyway depth exceeds shaft radius")
    if chamfer <= 0:
        errors.append("Chamfer must be greater than zero")
    return errors


def _validate_bracket(width, depth, thickness, support_thickness):
    errors = []
    if support_thickness >= thickness:
        errors.append("Support thickness must be less than main thickness")
    if width <= 0 or depth <= 0:
        errors.append("Bracket dimensions must be positive")
    return errors


def _validate_base_plate(width, length, thickness, hole_dia):
    errors = []
    if hole_dia >= thickness:
        errors.append("Mounting hole diameter exceeds plate thickness")
    if hole_dia > min(width, length) / 4:
        errors.append("Mounting hole diameter too large for footprint")
    return errors


# ============================================================================
# DXF GENERATION UTILITIES
# ============================================================================
def _fmt(value):
    return f"{float(value):.4f}"


def _dxf_line(x1, y1, x2, y2, layer="0", linetype="CONTINUOUS"):
    return (
        f"0\nLINE\n8\n{layer}\n6\n{linetype}\n"
        f"10\n{_fmt(x1)}\n20\n{_fmt(y1)}\n30\n0\n"
        f"11\n{_fmt(x2)}\n21\n{_fmt(y2)}\n31\n0\n"
    )


def _dxf_circle(x, y, radius, layer="0"):
    return (
        f"0\nCIRCLE\n8\n{layer}\n6\nCONTINUOUS\n"
        f"10\n{_fmt(x)}\n20\n{_fmt(y)}\n30\n0\n40\n{_fmt(radius)}\n"
    )


def _dxf_text(x, y, value, height=2.5):
    return (
        f"0\nTEXT\n8\nDIMENSIONS\n10\n{_fmt(x)}\n20\n{_fmt(y)}\n30\n0\n"
        f"40\n{_fmt(height)}\n1\n{value}\n50\n0\n"
    )


def _dimension(entities, x1, y1, x2, y2, label, text_x, text_y):
    entities.append(_dxf_line(x1, y1, x2, y2, "DIMENSIONS"))
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length:
        ux, uy = dx / length, dy / length
        size = min(2.5, max(0.8, length * 0.035))
        for x, y, direction in ((x1, y1, 1), (x2, y2, -1)):
            tip_x, tip_y = x + ux * size * direction, y + uy * size * direction
            wing = size * 0.4
            entities.append(_dxf_line(x, y, tip_x - uy * wing, tip_y + ux * wing, "DIMENSIONS"))
            entities.append(_dxf_line(x, y, tip_x + uy * wing, tip_y - ux * wing, "DIMENSIONS"))
    entities.append(_dxf_text(text_x, text_y, label))


def _dxf_document(component, geometry, dimensions):
    return (
        "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n"
        "9\n$MEASUREMENT\n70\n1\n9\n$LUNITS\n70\n2\n0\nENDSEC\n"
        "0\nSECTION\n2\nTABLES\n"
        "0\nTABLE\n2\nLTYPE\n70\n3\n"
        "0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0\n"
        "0\nLTYPE\n2\nHIDDEN\n70\n0\n3\nDashed line\n72\n65\n73\n2\n40\n6.0\n49\n4.0\n74\n0\n49\n-2.0\n74\n0\n"
        "0\nLTYPE\n2\nCENTER\n70\n0\n3\nCenter dash-dot\n72\n65\n73\n4\n40\n10.0\n49\n6.0\n74\n0\n49\n-2.0\n74\n0\n49\n1.0\n74\n0\n49\n-1.0\n74\n0\n0\nENDTAB\n"
        "0\nTABLE\n2\nLAYER\n70\n4\n"
        "0\nLAYER\n2\n0\n70\n0\n62\n7\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nDIMENSIONS\n70\n0\n62\n1\n6\nCONTINUOUS\n"
        "0\nLAYER\n2\nHIDDEN\n70\n0\n62\n8\n6\nHIDDEN\n"
        "0\nLAYER\n2\nCENTERLINE\n70\n0\n62\n4\n6\nCENTER\n"
        "0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"
        f"999\nCOMPONENT={component}\n"
        + "".join(geometry)
        + "".join(dimensions)
        + "0\nENDSEC\n0\nEOF\n"
    )


# ============================================================================
# FLANGE DXF GENERATION
# ============================================================================
def _flange_dxf(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height):
    geometry = []
    dimensions = []
    outer_r, bore_r, hub_r = outer_dia / 2, inner_dia / 2, hub_dia / 2
    neck_top_r = inner_dia / 2 + 3
    pcd_dia = (outer_dia + hub_dia) / 2
    top_x, top_y = outer_r + 25, outer_r + 35
    side_x, side_y = top_x + outer_dia + 45, 15
    side_center = side_x + outer_r
    side_top, neck_top = side_y + thickness, side_y + thickness + hub_height

    dimensions.extend((_dxf_text(top_x - 12, top_y + outer_r + 20, "TOP VIEW", 3.5), _dxf_text(side_x, neck_top + 18, "SIDE VIEW", 3.5)))
    geometry.extend((_dxf_circle(top_x, top_y, outer_r), _dxf_circle(top_x, top_y, bore_r)))
    geometry.append(_dxf_circle(top_x, top_y, pcd_dia / 2, "CENTERLINE"))
    geometry.extend((
        _dxf_line(top_x - outer_r - 8, top_y, top_x + outer_r + 8, top_y, "CENTERLINE", "CENTER"),
        _dxf_line(top_x, top_y - outer_r - 8, top_x, top_y + outer_r + 8, "CENTERLINE", "CENTER"),
    ))
    for index in range(bolt_count):
        angle = math.tau * index / bolt_count
        hole_x = top_x + pcd_dia / 2 * math.cos(angle)
        hole_y = top_y + pcd_dia / 2 * math.sin(angle)
        geometry.append(_dxf_circle(hole_x, hole_y, bolt_dia / 2))
        geometry.extend((
            _dxf_line(hole_x - 4, hole_y, hole_x + 4, hole_y, "CENTERLINE", "CENTER"),
            _dxf_line(hole_x, hole_y - 4, hole_x, hole_y + 4, "CENTERLINE", "CENTER"),
        ))
    _dimension(dimensions, top_x - outer_r, top_y + outer_r + 9, top_x + outer_r, top_y + outer_r + 9, f"OD {outer_dia} mm", top_x - 13, top_y + outer_r + 13)
    _dimension(dimensions, top_x - bore_r, top_y - outer_r - 9, top_x + bore_r, top_y - outer_r - 9, f"BORE {inner_dia} mm", top_x - 15, top_y - outer_r - 15)
    _dimension(dimensions, top_x - pcd_dia / 2, top_y + outer_r + 24, top_x + pcd_dia / 2, top_y + outer_r + 24, f"PCD {pcd_dia:g} mm | {bolt_count} x {bolt_dia}", top_x - 25, top_y + outer_r + 28)

    geometry.extend((
        _dxf_line(side_x, side_y, side_x + outer_dia, side_y),
        _dxf_line(side_x, side_y, side_x, side_top),
        _dxf_line(side_x + outer_dia, side_y, side_x + outer_dia, side_top),
        _dxf_line(side_x, side_top, side_x + outer_dia, side_top),
        _dxf_line(side_center - hub_r, side_top, side_center - neck_top_r, neck_top),
        _dxf_line(side_center + hub_r, side_top, side_center + neck_top_r, neck_top),
        _dxf_line(side_center - neck_top_r, neck_top, side_center + neck_top_r, neck_top),
        _dxf_line(side_center - bore_r, side_y, side_center - bore_r, neck_top),
        _dxf_line(side_center + bore_r, side_y, side_center + bore_r, neck_top),
        _dxf_line(side_x - 8, side_y + thickness / 2, side_x + outer_dia + 8, side_y + thickness / 2, "CENTERLINE", "CENTER"),
    ))
    for index in range(bolt_count):
        angle = math.tau * index / bolt_count
        center_x = side_center + pcd_dia / 2 * math.cos(angle)
        geometry.extend((
            _dxf_line(center_x - bolt_dia / 2, side_y, center_x - bolt_dia / 2, side_top, "HIDDEN", "HIDDEN"),
            _dxf_line(center_x + bolt_dia / 2, side_y, center_x + bolt_dia / 2, side_top, "HIDDEN", "HIDDEN"),
        ))
    _dimension(dimensions, side_x - 12, side_y, side_x - 12, side_top, f"THICKNESS {thickness} mm", side_x - 25, side_y + thickness / 2)
    _dimension(dimensions, side_center - hub_r, side_top + 6, side_center + hub_r, side_top + 6, f"HUB DIA {hub_dia} mm", side_center - hub_r, side_top + 10)
    _dimension(dimensions, side_center - neck_top_r, neck_top + 7, side_center + neck_top_r, neck_top + 7, f"NECK DIA {neck_top_r * 2:g} mm", side_center - neck_top_r, neck_top + 11)
    _dimension(dimensions, side_x + outer_dia + 18, side_top, side_x + outer_dia + 18, neck_top, f"HUB HEIGHT {hub_height} mm", side_x + outer_dia + 21, side_top + hub_height / 2)
    dimensions.append(_dxf_text(side_x, side_y - 7, f"{bolt_count} HOLES DIA {bolt_dia} mm", 2.5))
    return _dxf_document("FLANGE", geometry, dimensions)


# ============================================================================
# SHAFT DXF GENERATION
# ============================================================================
def _shaft_dxf(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth):
    geometry = []
    dimensions = []
    r1, r2 = dia1 / 2, dia2 / 2
    origin_x, axis_y = 20, r1 + 30
    total = len1 + len2
    key_start, key_end = (len1 - key_len) / 2, (len1 + key_len) / 2
    profile = (
        (0, -r1 + chamfer), (chamfer, -r1), (len1, -r1), (len1, -r2),
        (total - chamfer, -r2), (total, -r2 + chamfer), (total, r2 - chamfer),
        (total - chamfer, r2), (len1, r2), (len1, r1), (key_end, r1),
        (key_end, r1 - key_depth), (key_start, r1 - key_depth),
        (key_start, r1), (chamfer, r1), (0, r1 - chamfer),
    )
    dimensions.extend((_dxf_text(origin_x, axis_y + r1 + 25, "SIDE PROFILE", 3.5), _dxf_text(origin_x + total + r1 + 25, axis_y + r1 + 25, "END VIEW", 3.5)))
    for index, point in enumerate(profile):
        next_point = profile[(index + 1) % len(profile)]
        geometry.append(_dxf_line(origin_x + point[0], axis_y + point[1], origin_x + next_point[0], axis_y + next_point[1]))
    geometry.append(_dxf_line(origin_x - 8, axis_y, origin_x + total + 8, axis_y, "CENTERLINE", "CENTER"))
    geometry.extend((
        _dxf_line(origin_x + key_start, axis_y + r1 - key_depth, origin_x + key_end, axis_y + r1 - key_depth, "HIDDEN", "HIDDEN"),
        _dxf_line(origin_x + key_start, axis_y + r1 - key_depth, origin_x + key_start, axis_y + r1, "HIDDEN", "HIDDEN"),
        _dxf_line(origin_x + key_end, axis_y + r1 - key_depth, origin_x + key_end, axis_y + r1, "HIDDEN", "HIDDEN"),
    ))
    _dimension(dimensions, origin_x, axis_y + r1 + 9, origin_x + len1, axis_y + r1 + 9, f"LENGTH 1 {len1} mm", origin_x + len1 / 2 - 12, axis_y + r1 + 13)
    _dimension(dimensions, origin_x + len1, axis_y + r1 + 9, origin_x + total, axis_y + r1 + 9, f"LENGTH 2 {len2} mm", origin_x + len1 + len2 / 2 - 12, axis_y + r1 + 13)
    _dimension(dimensions, origin_x - 12, axis_y - r1, origin_x - 12, axis_y + r1, f"DIA 1 {dia1} mm", origin_x - 28, axis_y)
    _dimension(dimensions, origin_x + total + 12, axis_y - r2, origin_x + total + 12, axis_y + r2, f"DIA 2 {dia2} mm", origin_x + total + 16, axis_y)
    _dimension(dimensions, origin_x + key_start, axis_y - r1 - 12, origin_x + key_end, axis_y - r1 - 12, f"KEYWAY LENGTH {key_len} mm", origin_x + key_start, axis_y - r1 - 17)
    dimensions.append(_dxf_text(origin_x + len1 / 2, axis_y + r1 + 20, f"KEY WIDTH {key_width} / DEPTH {key_depth} mm", 2.5))
    dimensions.append(_dxf_text(origin_x + total - chamfer * 2, axis_y - r2 - 7, f"CHAMFER {chamfer:g} mm BOTH ENDS", 2.5))

    end_x = origin_x + total + 35 + r1
    geometry.extend((_dxf_circle(end_x, axis_y, r1),
        _dxf_line(end_x - r1 - 7, axis_y, end_x + r1 + 7, axis_y, "CENTERLINE", "CENTER"),
        _dxf_line(end_x, axis_y - r1 - 7, end_x, axis_y + r1 + 7, "CENTERLINE", "CENTER")))
    half_width = key_width / 2
    slot_edge_y = axis_y + math.sqrt(r1 * r1 - half_width * half_width)
    floor_y = axis_y + r1 - key_depth
    geometry.extend((
        _dxf_line(end_x - half_width, slot_edge_y, end_x - half_width, floor_y),
        _dxf_line(end_x + half_width, slot_edge_y, end_x + half_width, floor_y),
        _dxf_line(end_x - half_width, floor_y, end_x + half_width, floor_y),
    ))
    _dimension(dimensions, end_x - half_width, axis_y + r1 + 9, end_x + half_width, axis_y + r1 + 9, f"WIDTH {key_width} mm", end_x - half_width, axis_y + r1 + 13)
    _dimension(dimensions, end_x + r1 + 9, floor_y, end_x + r1 + 9, axis_y + r1, f"DEPTH {key_depth} mm", end_x + r1 + 12, axis_y + r1 - key_depth / 2)
    return _dxf_document("STEPPED_SHAFT", geometry, dimensions)


# ============================================================================
# SCAD GENERATION
# ============================================================================
def _flange_scad(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height):
    pcd_dia = (outer_dia + hub_dia) / 2
    return f"""outer_dia = {outer_dia};
inner_dia = {inner_dia};
thickness = {thickness};
bolt_count = {bolt_count};
bolt_dia = {bolt_dia};
hub_dia = {hub_dia};
hub_height = {hub_height};
bolt_circle_dia = {pcd_dia};
neck_top_dia = inner_dia + 6;
$fn = 128;

difference() {{
    union() {{
        cylinder(h = thickness, d = outer_dia);
        translate([0, 0, thickness])
            cylinder(h = hub_height, d1 = hub_dia, d2 = neck_top_dia);
    }}
    translate([0, 0, -1])
        cylinder(h = thickness + hub_height + 2, d = inner_dia);
    for (i = [0 : bolt_count - 1]) {{
        rotate([0, 0, i * 360 / bolt_count])
            translate([bolt_circle_dia / 2, 0, -1])
                cylinder(h = thickness + 2, d = bolt_dia);
    }}
}}
"""


def _shaft_scad(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth):
    return f"""len1 = {len1};
dia1 = {dia1};
len2 = {len2};
dia2 = {dia2};
chamfer = {chamfer};
keyway_length = {key_len};
keyway_width = {key_width};
keyway_depth = {key_depth};
total_length = len1 + len2;
$fn = 128;

difference() {{
    union() {{
        cylinder(h = chamfer, d1 = dia1 - 2 * chamfer, d2 = dia1);
        translate([0, 0, chamfer]) cylinder(h = len1 - chamfer, d = dia1);
        translate([0, 0, len1]) cylinder(h = len2 - chamfer, d = dia2);
        translate([0, 0, total_length - chamfer])
            cylinder(h = chamfer, d1 = dia2, d2 = dia2 - 2 * chamfer);
    }}
    translate([-keyway_width / 2, dia1 / 2 - keyway_depth, (len1 - keyway_length) / 2])
        cube([keyway_width, keyway_depth + dia1 / 2, keyway_length]);
}}
"""


def _bracket_scad(width, depth, thickness, support_thickness):
    return f"""width = {width};
depth = {depth};
thickness = {thickness};
support_thickness = {support_thickness};
$fn = 128;

difference() {{
    cube([width, depth, thickness]);
    translate([thickness, thickness, -1])
        cube([width - 2 * thickness, depth - 2 * thickness, thickness + 2]);
}}
"""


def _base_plate_scad(width, length, thickness, hole_dia):
    return f"""width = {width};
length = {length};
thickness = {thickness};
hole_dia = {hole_dia};
$fn = 128;

difference() {{
    cube([width, length, thickness]);
    translate([width / 2, length / 2, -1])
        cylinder(h = thickness + 2, d = hole_dia);
}}
"""


# ============================================================================
# MAIN PAGE CONFIG AND STYLES
# ============================================================================
st.set_page_config(page_title="Forge CAD CAM", page_icon="F", layout="wide")

st.markdown(
    """
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    html, body, [data-testid="stAppViewContainer"] {
        height: 100vh;
        overflow: hidden;
    }
    [data-testid="stAppViewContainer"] {
        display: flex;
        flex-direction: column;
    }
    [data-testid="stMainBlockContainer"] {
        flex: 1;
        overflow: hidden;
    }
    .top-header {
        background: #0f0f0f;
        border-bottom: 2px solid #f59e0b;
        padding: 0.75rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .header-branding {
        font-weight: 800;
        font-size: 1.1rem;
        color: #fbbf24;
        letter-spacing: 0.02em;
    }
    .header-divider {
        width: 1px;
        height: 24px;
        background: #f59e0b;
    }
    .header-user {
        color: #e5e7eb;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .header-tier {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid #f59e0b;
        color: #fcd34d;
        padding: 0.35rem 0.75rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .login-container {
        width: 100%;
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #1f1f1f 0%, #0f0f0f 100%);
    }
    .login-box {
        background: #111111;
        border: 3px solid #f59e0b;
        border-radius: 12px;
        padding: 2.5rem;
        width: 360px;
        box-shadow: 0 0 0 2px #000, 0 20px 40px rgba(245, 158, 11, 0.25);
    }
    .login-box h2 {
        color: #fbbf24;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
        font-weight: 800;
        letter-spacing: 0.01em;
    }
    .login-box p {
        color: #9ca3af;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 1.75rem;
    }
    .layout-container {
        display: flex;
        flex: 1;
        overflow: hidden;
        gap: 0;
    }
    .sidebar-column {
        width: 30%;
        background: #0f0f0f;
        border-right: 2px solid #f59e0b;
        overflow-y: auto;
        padding: 1.5rem;
    }
    .main-column {
        width: 70%;
        background: #0b0b0b;
        overflow-y: auto;
        padding: 1.5rem;
    }
    .catalogue-container {
        background: #1a1a1a;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        height: 240px;
        overflow-y: auto;
        margin-bottom: 1.5rem;
        padding: 0.75rem;
    }
    .catalogue-container::-webkit-scrollbar {
        width: 8px;
    }
    .catalogue-container::-webkit-scrollbar-track {
        background: #111111;
        border-radius: 4px;
    }
    .catalogue-container::-webkit-scrollbar-thumb {
        background: #f59e0b;
        border-radius: 4px;
    }
    .catalogue-container::-webkit-scrollbar-thumb:hover {
        background: #fbbf24;
    }
    .sidebar-label {
        color: #fbbf24;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.01em;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
    }
    .parameter-tabs {
        margin-top: 1.5rem;
    }
    .spec-table {
        background: #1a1a1a;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .spec-table h3 {
        color: #fbbf24;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: 0.01em;
    }
    .spec-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #333333;
    }
    .spec-row:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .spec-label {
        color: #e5e7eb;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .spec-value {
        color: #fcd34d;
        font-size: 0.9rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
    }
    .float-taskbar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: #0b0b0b;
        border-top: 3px solid #f59e0b;
        padding: 0.75rem 1.5rem;
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 1rem;
        z-index: 999;
    }
    .taskbar-button {
        height: 45px;
        min-width: 220px;
        background: #f59e0b;
        color: #0b0b0b;
        border: none;
        border-radius: 6px;
        font-weight: 800;
        font-size: 0.9rem;
        cursor: pointer;
        padding: 0 1.25rem;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    .taskbar-button:hover {
        background: #fbbf24;
        transform: translateY(-2px);
    }
    .taskbar-button:active {
        transform: translateY(0);
    }
    .validation-error {
        background: rgba(239, 68, 68, 0.1);
        border: 2px solid #ef4444;
        border-radius: 6px;
        padding: 0.75rem;
        color: #fca5a5;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    [data-testid="stTabs"] {
        margin-top: 1rem;
    }
    .stTabs [role="tablist"] {
        gap: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_init_auth_state()

# ============================================================================
# AUTHENTICATION FLOW
# ============================================================================
if not st.session_state.auth_user:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            '<div class="login-box"><h2>Forge CAD CAM</h2><p>Engineering System Access</p></div>',
            unsafe_allow_html=True,
        )
        username_input = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password_input = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Sign In", use_container_width=True, type="primary"):
                if _authenticate_user(username_input, password_input):
                    st.success("Welcome to Forge CAD CAM!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try again.")
        with col_btn2:
            st.button("Demo Access", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# AUTHENTICATED LAYOUT
# ============================================================================
st.markdown(
    f"""
    <div class="top-header">
        <div class="header-left">
            <div class="header-branding">⚙ FORGE CAD CAM</div>
            <div class="header-divider"></div>
            <div class="header-user">User: <strong>{st.session_state.auth_user}</strong></div>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="header-tier">✓ AUTHORIZED ENGINEER</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="layout-container">', unsafe_allow_html=True)

# ============================================================================
# SIDEBAR (30%)
# ============================================================================
st.markdown('<div class="sidebar-column">', unsafe_allow_html=True)

st.markdown('<div class="sidebar-label">Component Catalogue</div>', unsafe_allow_html=True)

catalogue_items = ["Flange", "Stepped Shaft", "Industrial Bracket", "Base Plate", "Custom Part Coming Soon"]
selected_component = st.selectbox(
    "Select Component",
    catalogue_items,
    index=catalogue_items.index(st.session_state.selected_component) if st.session_state.selected_component in catalogue_items else 0,
    label_visibility="collapsed",
    key="component_select",
)

if selected_component != st.session_state.selected_component:
    st.session_state.selected_component = selected_component

component = selected_component
params = {}
validation_errors = []
scad_text = ""
dxf_text = ""
filename = ""

# ====================================================================
# FLANGE CONFIGURATION
# ====================================================================
if component == "Flange":
    tab1, tab2 = st.tabs(["Main Geometry", "Internal Details & Features"])

    with tab1:
        st.markdown("**Outer Envelope**")
        outer_dia = st.slider("Outer diameter (mm)", 80, 300, 200, key="flange_outer")
        inner_max = min(90, outer_dia - 40)
        inner_dia = st.slider("Bore diameter (mm)", 20, inner_max, min(50, inner_max), key="flange_bore")
        thickness = st.slider("Plate thickness (mm)", 10, 40, 20, key="flange_thickness")

    with tab2:
        st.markdown("**Bolt Configuration**")
        bolt_count = st.slider("Bolt hole count", 4, 12, 6, key="flange_bolt_count")
        bolt_dia = st.slider("Bolt hole diameter (mm)", 6, 24, 12, key="flange_bolt_diameter")

        st.markdown("**Hub Weld Neck**")
        hub_min, hub_max = inner_dia + 10, outer_dia - 30
        hub_dia = st.slider("Weld neck base diameter (mm)", hub_min, hub_max, min(max(90, hub_min), hub_max), key="flange_hub_diameter")
        hub_height = st.slider("Weld neck height (mm)", 10, 50, 25, key="flange_hub_height")

    validation_errors = _validate_flange(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height)
    pcd_dia = (outer_dia + hub_dia) / 2
    params = {
        "Outer diameter": f"{outer_dia} mm",
        "Bore diameter": f"{inner_dia} mm",
        "Plate thickness": f"{thickness} mm",
        "Bolt hole count": f"{bolt_count} holes",
        "Bolt hole diameter": f"{bolt_dia} mm",
        "Pitch circle diameter": f"{pcd_dia:g} mm",
        "Weld neck base diameter": f"{hub_dia} mm",
        "Weld neck top diameter": f"{inner_dia + 6} mm",
        "Weld neck height": f"{hub_height} mm",
        "Overall height": f"{thickness + hub_height} mm",
    }

    if not validation_errors:
        scad_text = _flange_scad(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height)
        dxf_text = _flange_dxf(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height)
    filename = "flange"

# ====================================================================
# STEPPED SHAFT CONFIGURATION
# ====================================================================
elif component == "Stepped Shaft":
    tab1, tab2 = st.tabs(["Main Geometry", "Internal Details & Features"])

    with tab1:
        st.markdown("**Section 1 (Large Diameter)**")
        len1 = st.slider("Section 1 length (mm)", 20, 120, 50, key="shaft_len1")
        dia1 = st.slider("Section 1 diameter (mm)", 30, 100, 50, key="shaft_dia1")

        st.markdown("**Section 2 (Small Diameter)**")
        len2 = st.slider("Section 2 length (mm)", 20, 120, 40, key="shaft_len2")
        dia2_max = dia1 - 6
        dia2 = st.slider("Section 2 diameter (mm)", 10, dia2_max, min(30, dia2_max), key="shaft_dia2")

    with tab2:
        st.markdown("**End Treatment**")
        chamfer = st.slider("End chamfer (mm)", 0.5, 4.0, 1.5, step=0.5, key="shaft_chamfer")

        st.markdown("**Keyway Configuration**")
        key_len = st.slider("Keyway length (mm)", 10, len1 - 10, min(25, len1 - 10), key="shaft_key_length")
        key_width = st.slider("Keyway width (mm)", 2, min(12, dia1 - 2), 6, key="shaft_key_width")
        key_depth = st.slider("Keyway depth (mm)", 2, min(8, dia1 // 2 - 2), 4, key="shaft_key_depth")

    validation_errors = _validate_shaft(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth)
    params = {
        "Section 1 length": f"{len1} mm",
        "Section 1 diameter": f"{dia1} mm",
        "Section 2 length": f"{len2} mm",
        "Section 2 diameter": f"{dia2} mm",
        "End chamfer": f"{chamfer:g} mm",
        "Keyway length": f"{key_len} mm",
        "Keyway width": f"{key_width} mm",
        "Keyway depth": f"{key_depth} mm",
        "Overall length": f"{len1 + len2} mm",
        "Diameter step": f"{dia1 - dia2} mm",
    }

    if not validation_errors:
        scad_text = _shaft_scad(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth)
        dxf_text = _shaft_dxf(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth)
    filename = "stepped_shaft"

# ====================================================================
# INDUSTRIAL BRACKET CONFIGURATION
# ====================================================================
elif component == "Industrial Bracket":
    tab1, tab2 = st.tabs(["Main Geometry", "Internal Details & Features"])

    with tab1:
        st.markdown("**Outer Profile**")
        width = st.slider("Width (mm)", 50, 200, 100, key="bracket_width")
        depth = st.slider("Depth (mm)", 50, 200, 100, key="bracket_depth")
        thickness = st.slider("Main thickness (mm)", 5, 25, 10, key="bracket_thickness")

    with tab2:
        st.markdown("**Internal Support**")
        support_thickness = st.slider("Support thickness (mm)", 1, 15, 5, key="bracket_support_thickness")

    validation_errors = _validate_bracket(width, depth, thickness, support_thickness)
    params = {
        "Width": f"{width} mm",
        "Depth": f"{depth} mm",
        "Main thickness": f"{thickness} mm",
        "Support thickness": f"{support_thickness} mm",
        "Cavity width": f"{width - 2 * thickness} mm",
        "Cavity depth": f"{depth - 2 * thickness} mm",
    }

    if not validation_errors:
        scad_text = _bracket_scad(width, depth, thickness, support_thickness)
    filename = "bracket"

# ====================================================================
# BASE PLATE CONFIGURATION
# ====================================================================
elif component == "Base Plate":
    tab1, tab2 = st.tabs(["Main Geometry", "Internal Details & Features"])

    with tab1:
        st.markdown("**Main Footprint**")
        width = st.slider("Width (mm)", 100, 400, 200, key="base_width")
        length = st.slider("Length (mm)", 100, 400, 250, key="base_length")
        thickness = st.slider("Thickness (mm)", 5, 30, 10, key="base_thickness")

    with tab2:
        st.markdown("**Mounting Holes**")
        hole_dia = st.slider("Mounting hole diameter (mm)", 5, 20, 10, key="base_hole_diameter")

    validation_errors = _validate_base_plate(width, length, thickness, hole_dia)
    params = {
        "Width": f"{width} mm",
        "Length": f"{length} mm",
        "Thickness": f"{thickness} mm",
        "Mounting hole diameter": f"{hole_dia} mm",
        "Footprint area": f"{width * length} mm²",
        "Volume": f"{width * length * thickness} mm³",
    }

    if not validation_errors:
        scad_text = _base_plate_scad(width, length, thickness, hole_dia)
    filename = "base_plate"

else:
    st.warning("Selected item is not available yet. Please choose an available component.")
    st.session_state.selected_component = "Flange"
    component = "Flange"

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT AREA (70%)
# ============================================================================
st.markdown('<div class="main-column">', unsafe_allow_html=True)

st.markdown("### Premium Engineering Specification Report")

if validation_errors:
    for error in validation_errors:
        st.markdown(f'<div class="validation-error">⚠ {error}</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="background: #1a1a1a; border: 2px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
        <div style="color: #fbbf24; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem;">
            ✓ CAD CAM CORE ENGINE ACTIVE
        </div>
        <div style="color: #10b981; font-weight: 600; font-size: 0.85rem;">
            Geometry calculated successfully for: <strong>{component}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="spec-table">', unsafe_allow_html=True)
st.markdown('<h3>Active Configuration Parameters</h3>', unsafe_allow_html=True)

if params:
    for name, value in params.items():
        st.markdown(
            f"""
            <div class="spec-row">
                <div class="spec-label">{name}</div>
                <div class="spec-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# FLOATING TASKBAR
# ============================================================================
st.markdown('<div class="float-taskbar">', unsafe_allow_html=True)

col_3d, col_2d, col_logout = st.columns(3)

with col_3d:
    if scad_text and not validation_errors:
        st.download_button(
            "📥 Download 3D Model (.scad)",
            data=scad_text,
            file_name=f"{filename}.scad",
            mime="text/plain",
            key="download_scad",
            use_container_width=True,
        )
    else:
        st.markdown('<button class="taskbar-button" disabled>📥 Download 3D Model (.scad)</button>', unsafe_allow_html=True)

with col_2d:
    if dxf_text and not validation_errors:
        st.download_button(
            "📥 Download 2D Drawing (.dxf)",
            data=dxf_text,
            file_name=f"{filename}.dxf",
            mime="application/dxf",
            key="download_dxf",
            use_container_width=True,
        )
    else:
        st.markdown('<button class="taskbar-button" disabled>📥 Download 2D Drawing (.dxf)</button>', unsafe_allow_html=True)

with col_logout:
    if st.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
        _logout_user()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
