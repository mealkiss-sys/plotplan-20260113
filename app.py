import json
import uuid
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Plant PlotPlan", layout="wide")

# ---------------------------
# Utils
# ---------------------------
TYPE_STYLE = {
    "건물": {"fill": "rgba(0, 120, 255, 0.25)", "stroke": "rgba(0, 120, 255, 0.9)"},
    "도로": {"fill": "rgba(80, 80, 80, 0.25)", "stroke": "rgba(80, 80, 80, 0.9)"},
    "담장": {"fill": "rgba(255, 180, 0, 0.15)", "stroke": "rgba(255, 180, 0, 0.95)"},
    "문":   {"fill": "rgba(0, 200, 120, 0.20)", "stroke": "rgba(0, 200, 120, 0.95)"},
}

def ensure_state():
    if "site" not in st.session_state:
        st.session_state.site = {"w_m": 80.0, "h_m": 60.0}
    if "scale" not in st.session_state:
        st.session_state.scale = 10  # px per meter
    if "objects" not in st.session_state:
        # fabric.js objects list
        st.session_state.objects = []
    if "finished" not in st.session_state:
        st.session_state.finished = False

def make_rect_obj(obj_type: str, w_m: float, h_m: float, x_px: float, y_px: float, scale: float):
    style = TYPE_STYLE[obj_type]
    w = w_m * scale
    h = h_m * scale
    return {
        "type": "rect",
        "version": "4.6.0",
        "originX": "left",
        "originY": "top",
        "left": x_px,
        "top": y_px,
        "width": w,
        "height": h,
        "fill": style["fill"],
        "stroke": style["stroke"],
        "strokeWidth": 2,
        "strokeUniform": True,
        "rx": 0,
        "ry": 0,
        "angle": 0,
        "opacity": 1,
        "shadow": None,
        "visible": True,
        "backgroundColor": "",
        "globalCompositeOperation": "source-over",
        "transformMatrix": None,
        "skewX": 0,
        "skewY": 0,
        "scaleX": 1,
        "scaleY": 1,
        "flipX": False,
        "flipY": False,
        "name": obj_type,
        "id": str(uuid.uuid4()),
        # custom meta
        "meta": {"type": obj_type, "w_m": w_m, "h_m": h_m},
    }

def boundary_rect(site_w_m: float, site_h_m: float, scale: float):
    # draw as a non-selectable frame
    return {
        "type": "rect",
        "version": "4.6.0",
        "originX": "left",
        "originY": "top",
        "left": 0,
        "top": 0,
        "width": site_w_m * scale,
        "height": site_h_m * scale,
        "fill": "rgba(0,0,0,0)",
        "stroke": "rgba(0,0,0,0.9)",
        "strokeWidth": 3,
        "strokeUniform": True,
        "selectable": False,
        "evented": False,
        "name": "부지경계",
        "id": "SITE_BOUNDARY",
        "meta": {"type": "부지경계", "w_m": site_w_m, "h_m": site_h_m},
    }

def clamp_inside_site(obj, site_w_px, site_h_px):
    # keep top-left inside; allow overflow check for width/height too
    left = max(0, min(obj.get("left", 0), site_w_px - (obj.get("width", 0) * obj.get("scaleX", 1))))
    top  = max(0, min(obj.get("top", 0),  site_h_px - (obj.get("height", 0) * obj.get("scaleY", 1))))
    obj["left"] = left
    obj["top"] = top
    return obj

# ---------------------------
# App
# ---------------------------
ensure_state()

st.title("⚡ Plant PlotPlan (웹UI)")

colL, colR = st.columns([1, 2], gap="large")

with colL:
    st.subheader("Step 1) 부지 경계 만들기")
    st.session_state.site["w_m"] = st.number_input("부지 가로(m)", min_value=1.0, value=float(st.session_state.site["w_m"]), step=1.0)
    st.session_state.site["h_m"] = st.number_input("부지 세로(m)", min_value=1.0, value=float(st.session_state.site["h_m"]), step=1.0)

    st.session_state.scale = st.slider("스케일 (px / m)", min_value=5, max_value=30, value=int(st.session_state.scale), step=1)

    st.divider()
    st.subheader("Step 2) 오브젝트 추가")
    option = st.selectbox("옵션 선택", ["1(건물)", "2(도로)", "3(담장)", "4(문)"])
    opt_map = {"1(건물)": "건물", "2(도로)": "도로", "3(담장)": "담장", "4(문)": "문"}
    obj_type = opt_map[option]

    w_m = st.number_input(f"{obj_type} 가로(m)", min_value=0.2, value=10.0, step=0.5)
    h_m = st.number_input(f"{obj_type} 세로(m)", min_value=0.2, value=6.0, step=0.5)

    help_txt = (
        "✅ 추가하면 캔버스 중앙에 생기고,\n"
        "마우스로 **왼쪽 클릭 드래그** 해서 이동 가능.\n"
        "오브젝트 선택 후 **모서리 핸들**로 크기 조절도 가능.\n"
        "선택한 상태에서 Delete는 브라우저/환경 따라 다를 수 있어서,\n"
        "삭제는 아래 '선택 오브젝트 삭제' 버튼으로 하는 걸 추천."
    )
    st.info(help_txt)

    add_btn = st.button("➕ 추가", use_container_width=True)

    st.divider()
    st.subheader("Step 3) 배치 완료/내보내기")
    finish_btn = st.button("✅ 배치 완료(Finish)", use_container_width=True)
    st.button("🔄 다시 시작(Reset)", use_container_width=True, on_click=lambda: st.session_state.update({"objects": [], "finished": False}))

with colR:
    site_w_px = st.session_state.site["w_m"] * st.session_state.scale
    site_h_px = st.session_state.site["h_m"] * st.session_state.scale

    # add object (center placement)
    if add_btn:
        cx = max(0, site_w_px / 2 - (w_m * st.session_state.scale) / 2)
        cy = max(0, site_h_px / 2 - (h_m * st.session_state.scale) / 2)
        new_obj = make_rect_obj(obj_type, float(w_m), float(h_m), cx, cy, st.session_state.scale)
        st.session_state.objects.append(new_obj)

    # Build initial drawing with boundary + objects
    drawing = {
        "version": "4.6.0",
        "objects": [boundary_rect(st.session_state.site["w_m"], st.session_state.site["h_m"], st.session_state.scale)]
                   + st.session_state.objects
    }

    st.subheader("배치 캔버스 (드래그로 이동/수정)")
    canvas_result = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=2,
        stroke_color="rgba(0,0,0,0.7)",
        background_color="#ffffff",
        update_streamlit=True,
        height=int(site_h_px) + 10,
        width=int(site_w_px) + 10,
        drawing_mode="transform",   # 핵심: 기존 오브젝트 이동/리사이즈
        initial_drawing=drawing,
        key="canvas",
    )

    # Sync canvas back to session
    if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
        objs = canvas_result.json_data["objects"]

        # 첫 번째는 SITE_BOUNDARY (non-selectable frame)
        filtered = []
        for o in objs:
            if o.get("id") == "SITE_BOUNDARY":
                continue
            # 안전하게 부지 안쪽으로 클램프
            filtered.append(clamp_inside_site(o, site_w_px, site_h_px))
        st.session_state.objects = filtered

    # Controls: delete selected object by id (simple)
    st.markdown("### 선택 오브젝트 삭제")
    # streamlit-drawable-canvas는 선택 객체 id를 따로 안 주는 경우가 많아서,
    # 리스트에서 id 선택 방식으로 제공 (확실하게 동작하게 하려고).
    if st.session_state.objects:
        id_to_name = {o.get("id", ""): o.get("name", "오브젝트") for o in st.session_state.objects}
        selected_id = st.selectbox("삭제할 오브젝트 선택", list(id_to_name.keys()), format_func=lambda x: f"{id_to_name[x]} ({x[:8]})")
        if st.button("🗑️ 삭제", use_container_width=True):
            st.session_state.objects = [o for o in st.session_state.objects if o.get("id") != selected_id]
            st.experimental_rerun()
    else:
        st.caption("아직 추가된 오브젝트가 없어~")

    # Finish
    if finish_btn:
        st.session_state.finished = True

    if st.session_state.finished:
        st.success("배치 완료! 아래에서 JSON/CSV로 내보낼 수 있어.")
        export = {
            "site": {
                "w_m": st.session_state.site["w_m"],
                "h_m": st.session_state.site["h_m"],
                "scale_px_per_m": st.session_state.scale,
            },
            "objects": st.session_state.objects,
        }
        st.download_button(
            "⬇️ JSON 다운로드",
            data=json.dumps(export, ensure_ascii=False, indent=2),
            file_name="plotplan.json",
            mime="application/json",
            use_container_width=True,
        )

        # also show simplified table-like text (type, meters, position meters)
        simple = []
        for o in st.session_state.objects:
            meta = o.get("meta", {})
            # position meters based on top-left
            left_m = (o.get("left", 0) / st.session_state.scale)
            top_m = (o.get("top", 0) / st.session_state.scale)
            w_px = o.get("width", 0) * o.get("scaleX", 1)
            h_px = o.get("height", 0) * o.get("scaleY", 1)
            simple.append({
                "type": meta.get("type", o.get("name", "")),
                "w_m": round(w_px / st.session_state.scale, 3),
                "h_m": round(h_px / st.session_state.scale, 3),
                "x_m(left)": round(left_m, 3),
                "y_m(top)": round(top_m, 3),
                "id": o.get("id", ""),
            })

        st.markdown("### 배치 리스트(요약)")
        st.dataframe(simple, use_container_width=True)
