import math

import streamlit as st


st.set_page_config(page_title="Forge CAD CAM", page_icon="F", layout="wide")

if "is_premium" not in st.session_state:
    st.session_state.is_premium = False

st.markdown(
    """
    <style>
    .block-container { padding-bottom: 7.5rem !important; }
    div.premium-pay-panel {
        background: #111111;
        border: 3px solid #f59e0b;
        padding: 1.1rem 1.25rem 1.25rem 1.25rem;
        border-radius: 10px;
        box-shadow: 0 0 0 2px #000, 0 12px 28px rgba(245, 158, 11, 0.35);
    }
    div.premium-pay-panel h3 {
        color: #fbbf24;
        margin: 0 0 0.35rem 0;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.01em;
    }
    div.premium-pay-panel p {
        color: #fde68a;
        margin: 0 0 0.85rem 0;
        font-weight: 600;
    }
    div.commercial-lock {
        background: #78350f;
        color: #fcd34d;
        font-weight: 800;
        text-align: center;
        padding: 0.9rem 1rem;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        letter-spacing: 0.02em;
    }
    div.download-taskbar-marker + div {
        position: fixed !important;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: #0b0b0b;
        border-top: 3px solid #f59e0b;
        padding: 0.85rem 1.5rem 1.1rem calc(min(21rem, 30vw) + 1.5rem);
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45);
    }
    @media (max-width: 768px) {
        div.download-taskbar-marker + div {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    _dimension(dimensions, top_x - pcd_dia / 2, top_y + outer_r + 24, top_x + pcd_dia / 2, top_y + outer_r + 24, f"PCD {pcd_dia:g} mm | {bolt_count} x DIA {bolt_dia}", top_x - 25, top_y + outer_r + 28)

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
    _dimension(dimensions, side_center - hub_r, side_top + 6, side_center + hub_r, side_top + 6, f"HUB BASE DIA {hub_dia} mm", side_center - hub_r, side_top + 10)
    _dimension(dimensions, side_center - neck_top_r, neck_top + 7, side_center + neck_top_r, neck_top + 7, f"NECK TOP DIA {neck_top_r * 2:g} mm", side_center - neck_top_r, neck_top + 11)
    _dimension(dimensions, side_x + outer_dia + 18, side_top, side_x + outer_dia + 18, neck_top, f"HUB HEIGHT {hub_height} mm", side_x + outer_dia + 21, side_top + hub_height / 2)
    dimensions.append(_dxf_text(side_x, side_y - 7, f"{bolt_count} HOLES, DIA {bolt_dia} mm", 2.5))
    return _dxf_document("FLANGE", geometry, dimensions)


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
    dimensions.append(_dxf_text(origin_x + len1 / 2, axis_y + r1 + 20, f"KEYWAY WIDTH {key_width} mm / DEPTH {key_depth} mm", 2.5))
    dimensions.append(_dxf_text(origin_x + total - chamfer * 2, axis_y - r2 - 7, f"45 DEG CHAMFER {chamfer:g} mm, BOTH ENDS", 2.5))

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


def _catalogue_changed():
    if st.session_state.component_catalogue not in ("Flange", "Stepped Shaft"):
        st.session_state.component_catalogue = "Flange"
        st.session_state.catalogue_notice = True


with st.sidebar:
    st.title("Forge CAD CAM")
    st.caption("OFFLINE PARAMETRIC CONFIGURATOR")
    selected_component = st.selectbox(
        "Component catalogue",
        ("Flange", "Stepped Shaft", "Bracket Coming Soon", "Base Plate Coming Soon", "Bearing Housing Coming Soon"),
        key="component_catalogue",
        on_change=_catalogue_changed,
        format_func=lambda item: item if item in ("Flange", "Stepped Shaft") else f"{item} - unavailable",
    )
    if st.session_state.get("catalogue_notice", False):
        st.warning("This catalogue item is not available yet. Select Flange or Stepped Shaft.")
        del st.session_state.catalogue_notice

    st.divider()
    st.subheader("Dimensions / mm")
    if selected_component == "Flange":
        outer_dia = st.slider("Outer diameter (mm)", 80, 300, 200, key="flange_outer")
        inner_max = min(90, outer_dia - 40)
        inner_dia = st.slider("Bore diameter (mm)", 20, inner_max, min(50, inner_max), key="flange_bore")
        thickness = st.slider("Plate thickness (mm)", 10, 40, 20, key="flange_thickness")
        bolt_count = st.slider("Bolt hole count", 4, 12, 6, key="flange_bolt_count")
        bolt_dia = st.slider("Bolt hole diameter (mm)", 6, 24, 12, key="flange_bolt_diameter")
        hub_min, hub_max = inner_dia + 10, outer_dia - 30
        hub_dia = st.slider("Weld neck base diameter (mm)", hub_min, hub_max, min(max(90, hub_min), hub_max), key="flange_hub_diameter")
        hub_height = st.slider("Weld neck height (mm)", 10, 50, 25, key="flange_hub_height")
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
        scad_text = _flange_scad(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height)
        dxf_text = _flange_dxf(outer_dia, inner_dia, thickness, bolt_count, bolt_dia, hub_dia, hub_height)
        filename = "flange"
    else:
        len1 = st.slider("Section 1 length (mm)", 20, 120, 50, key="shaft_len1")
        dia1 = st.slider("Section 1 diameter (mm)", 30, 100, 50, key="shaft_dia1")
        len2 = st.slider("Section 2 length (mm)", 20, 120, 40, key="shaft_len2")
        dia2_max = dia1 - 6
        dia2 = st.slider("Section 2 diameter (mm)", 10, dia2_max, min(30, dia2_max), key="shaft_dia2")
        chamfer = st.slider("End chamfer (mm)", 0.5, 4.0, 1.5, step=0.5, key="shaft_chamfer")
        key_len = st.slider("Keyway length (mm)", 10, len1 - 10, min(25, len1 - 10), key="shaft_key_length")
        key_width = st.slider("Keyway width (mm)", 2, min(12, dia1 - 2), 6, key="shaft_key_width")
        key_depth = st.slider("Keyway depth (mm)", 2, min(8, dia1 // 2 - 2), 4, key="shaft_key_depth")
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
        scad_text = _shaft_scad(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth)
        dxf_text = _shaft_dxf(len1, dia1, len2, dia2, chamfer, key_len, key_width, key_depth)
        filename = "stepped_shaft"

st.title("CAD CAM Control Center")
st.caption("Local geometry compilation / No visual previews")

if st.session_state.get("payment_notice"):
    st.success("Payment successful, welcome to Premium Access")
    del st.session_state.payment_notice

with st.container(border=True):
    st.badge("CAD CAM Core Engine Active", color="green")
    st.success("Geometry calculated successfully for the selected part.")
    st.caption(f"Selected component: {selected_component}")
    st.subheader("Active parameters")
    st.table([{"Parameter": name, "Value": value} for name, value in params.items()])

if not st.session_state.is_premium:
    st.markdown(
        """
        <div class="premium-pay-panel">
            <h3>Unlock Unlimited Manufacturing Downloads for 9.90 USD per Month</h3>
            <p>Simulated Stripe Checkout / PayPal gateway. Manufacturing exports stay locked until payment is processed.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Process Secure Payment", type="primary", width="stretch", key="process_secure_payment"):
        st.session_state.is_premium = True
        st.session_state.payment_notice = True
        st.toast("Payment successful, welcome to Premium Access")
        st.rerun()

st.markdown('<div class="download-taskbar-marker"></div>', unsafe_allow_html=True)
download_3d, download_2d = st.columns(2)
with download_3d:
    if st.session_state.is_premium:
        st.download_button(
            "Download 3D Model (.scad)",
            data=scad_text,
            file_name=f"{filename}.scad",
            mime="text/plain",
            width="stretch",
            key="download_scad",
        )
    else:
        st.markdown('<div class="commercial-lock">Commercial Access Locked</div>', unsafe_allow_html=True)
with download_2d:
    if st.session_state.is_premium:
        st.download_button(
            "Download 2D Drawing (.dxf)",
            data=dxf_text,
            file_name=f"{filename}.dxf",
            mime="application/dxf",
            width="stretch",
            key="download_dxf",
        )
    else:
        st.markdown('<div class="commercial-lock">Commercial Access Locked</div>', unsafe_allow_html=True)
