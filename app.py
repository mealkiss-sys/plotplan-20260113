# app.py
# 실행: streamlit run app.py

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Plot Plan (Python-run WebUI)", layout="wide")

# Streamlit-side Project Title input (can be changed anytime)
project_title = st.text_input("Project Title", value="My Project")

HTML_template = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Plot Plan</title>

  <script src="https://cdn.jsdelivr.net/npm/fabric@5.3.0/dist/fabric.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>

  <style>
    :root{--bg:#0b1220;--panel:#0f172a;--text:#e5e7eb;--muted:#94a3b8}
    *{box-sizing:border-box}
    body{margin:0;font-family:system-ui,Segoe UI,Roboto,"Noto Sans KR",Arial;background:#071028;color:var(--text)}
    .wrap{display:flex;height:100vh;overflow:hidden}
    .left{width:360px;padding:14px;background:rgba(17,24,39,0.72);overflow:auto;border-right:1px solid rgba(255,255,255,0.04)}
    .right{flex:1;padding:14px;overflow:auto;position:relative}
    h1{font-size:18px;margin:0 0 8px}
    h2{font-size:13px;color:var(--muted);margin:14px 0 6px}
    label{font-size:12px;color:var(--muted);display:block;margin-bottom:6px}
    input,select,textarea,button{font-size:13px}
    input,select,textarea{width:100%;padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.02);color:var(--text)}
    textarea{min-height:80px;resize:vertical}
    button{padding:10px;border-radius:8px;border:0;background:#2b6cb0;color:white;cursor:pointer}
    .btn2{background:#16a34a}.btn3{background:#dc2626}
    .canvasBox{background:#fff;border-radius:12px;padding:12px;box-shadow:0 12px 30px rgba(0,0,0,0.35)}
    .projectTitle{position:absolute;left:50%;transform:translateX(-50%);top:6px;z-index:1000;background:#fff;color:#0b1220;padding:8px 14px;border-radius:8px;font-weight:800;font-size:18px}
    .modalBack{position:fixed;inset:0;display:none;background:rgba(0,0,0,0.56);align-items:center;justify-content:center;z-index:2000}
    .modal{width:560px;max-width:94vw;background:#0f172a;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,0.06)}
    .grid{display:grid;grid-template-columns:repeat(10,1fr);gap:8px;margin-top:8px}
    .swatch{width:100%;aspect-ratio:1/1;border-radius:8px;border:2px solid rgba(255,255,255,0.06);cursor:pointer}
    .swatch.sel{outline:3px solid rgba(99,102,241,0.25)}
    .muted{color:var(--muted);font-size:12px}
    .rotRow{display:flex;gap:8px;margin-top:6px}
    .rotBtn{padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);color:#e5e7eb;cursor:pointer}
    .rotBtn:hover{background:rgba(255,255,255,0.07)}
  </style>
</head>

<body>
<div class="wrap">
  <div class="left">
    <h1>🏗️ Plot Plan (Python-run WebUI)</h1>

    <h2>Step 1) 부지</h2>
    <label>가로 W (m)</label>
    <input id="siteW" type="number" min="1" value="500" />
    <label style="margin-top:8px">세로 H (m)</label>
    <input id="siteH" type="number" min="1" value="300" />
    <div style="margin-top:8px"><button id="applySite">부지 적용</button></div>

    <h2>Step 2) 객체 추가</h2>
    <label>타입</label>
    <select id="objType"><option>건물</option><option>도로</option><option>담장</option><option>문</option></select>

    <div style="display:flex;gap:8px;margin-top:8px">
      <div style="flex:1"><label>가로 (m)</label><input id="objW" type="number" min="0.2" step="0.1" value="20" /></div>
      <div style="flex:1"><label>세로 (m)</label><input id="objH" type="number" min="0.2" step="0.1" value="10" /></div>
    </div>

    <div style="margin-top:8px"><button id="addObj" class="btn2">객체 추가</button></div>

    <h2 style="margin-top:12px">Remark</h2>
    <label>Remark 텍스트</label>
    <input id="remarkText" placeholder="메모 입력" />
    <div style="display:flex;gap:8px;margin-top:8px">
      <button id="addRemark" class="btn2">Add Remark</button>
    </div>

    <h2 style="margin-top:12px">Rotation</h2>
    <div class="rotRow">
      <button class="rotBtn" data-rot="90">↻ 90°</button>
      <button class="rotBtn" data-rot="180">↻ 180°</button>
      <button class="rotBtn" data-rot="-90">↺ 90°</button>
    </div>
    <div class="muted" style="margin-top:6px">선택 객체에 버튼 누르면 즉시 회전됨</div>

    <h2 style="margin-top:12px">Export / Reset</h2>
    <div style="display:flex;gap:8px;margin-top:6px">
      <button id="savePDF">PDF 저장</button>
      <button id="resetAll" class="btn3">Reset</button>
    </div>

    <div style="margin-top:12px" class="muted">
      • 더블클릭: 편집창 열기 (색상/텍스트)<br/>
      • Delete: 선택 객체 삭제 · Ctrl+Z: Undo<br/>
      • 부지는 드래그/선택 불가 · 객체는 크기변경 불가(이동/회전만)<br/>
      • Remark는 부지 밖으로도 이동 가능(캔버스 안에서는 항상 보이게)
    </div>
  </div>

  <div class="right">
    <div class="projectTitle">__PROJECT_TITLE__</div>
    <div class="canvasBox" style="padding-top:40px">
      <canvas id="c" width="1200" height="800"></canvas>
    </div>
  </div>
</div>

<!-- modal -->
<div id="modalBack" class="modalBack">
  <div class="modal">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div style="font-weight:800">객체 편집</div>
      <button id="modalClose">닫기</button>
    </div>

    <div style="margin-top:8px"><label>색상 (fill & stroke 동일)</label>
      <div class="grid" id="colorGrid"></div>
    </div>

    <div style="margin-top:8px"><label>텍스트 (객체 중앙 / 객체 밖으로 못 나감)</label><textarea id="labelText"></textarea></div>

    <div style="display:flex;gap:8px;margin-top:10px">
      <button id="applyEdit" class="btn2">적용</button>
      <button id="deleteSel" class="btn3">삭제(Delete)</button>
    </div>
  </div>
</div>

<script>
/* ---------- core state ---------- */
const canvas = new fabric.Canvas('c', { preserveObjectStacking:true, selection:true });
const STORAGE_KEY = "plotplan_state_v2_objects_only";
const UNDO_KEY = STORAGE_KEY + "_undo";

const palette = ["#1f2937","#111827","#0b1220","#334155","#475569","#64748b","#ef4444","#f97316","#f59e0b","#eab308","#84cc16","#22c55e","#10b981","#14b8a6","#06b6d4","#0ea5e9","#3b82f6","#6366f1","#8b5cf6","#a855f7","#d946ef","#ec4899","#f43f5e","#fb7185","#a3e635","#34d399","#60a5fa","#93c5fd","#fca5a5","#fde68a"];
const defaultByType = {"건물":{fill:"#3b82f6"},"도로":{fill:"#111827"},"담장":{fill:"#94a3b8"},"문":{fill:"#f59e0b"}};

let siteW = 500, siteH = 300, scale = 1;
let siteRect = null;

const PAD_LEFT = 40;
const PAD_TOP  = 100;
const PAD_RIGHT= 40;
const PAD_BOTTOM=40;

const undoStack = [];
const UNDO_LIMIT = 120;

/* ---------- helpers ---------- */
function rgba(hex,a){
  const h = hex.replace("#","");
  const r = parseInt(h.slice(0,2),16), g = parseInt(h.slice(2,4),16), b = parseInt(h.slice(4,6),16);
  return `rgba(${r},${g},${b},${a})`;
}
function canvasBounds(){ return {x1:0,y1:0,x2:canvas.getWidth(),y2:canvas.getHeight()}; }
function siteBounds(){
  const x1 = PAD_LEFT, y1 = PAD_TOP;
  const x2 = PAD_LEFT + siteW * scale;
  const y2 = PAD_TOP + siteH * scale;
  return {x1,y1,x2,y2};
}

function pushUndo(){
  try{
    const snap = canvas.toDatalessJSON(["ppType","ppMeta"]);
    const filtered = {...snap, objects:(snap.objects||[]).filter(o => !(o && o.ppType==="SITE"))};
    undoStack.push(filtered);
    if(undoStack.length>UNDO_LIMIT) undoStack.shift();
    localStorage.setItem(UNDO_KEY, JSON.stringify(undoStack));
  }catch(e){ console.warn(e); }
}
function undo(){
  if(undoStack.length===0) return;
  const prev = undoStack.pop();
  redrawSiteOnly();
  canvas.loadFromJSON(prev, ()=>{
    if(siteRect) canvas.sendToBack(siteRect);
    fixLoadedObjectsAfterRestore();
    canvas.discardActiveObject();
    validateCollisions();
    canvas.requestRenderAll();
    saveStateToStorage();
  });
  localStorage.setItem(UNDO_KEY, JSON.stringify(undoStack));
}

/* ---------- text fit + clip ---------- */
function fitFontSimple(text, w, h){
  const pad = 14;
  const W = Math.max(1, w - pad*2);
  const H = Math.max(1, h - pad*2);
  if(!text) return 18;
  for(let fs=22; fs>=8; fs--){
    const charsPerLine = Math.max(1, Math.floor(W / (fs*0.62)));
    const lines = Math.max(1, Math.ceil(text.length / charsPerLine));
    const needH = lines * (fs * 1.25);
    if(needH <= H) return fs;
  }
  return 8;
}
function applyTextboxLayout(tb, rectW, rectH){
  const pad = 14;
  const w = Math.max(10, rectW - pad*2);
  const h = Math.max(10, rectH - pad*2);

  tb.set({
    width: w,
    left: 0, top: 0,
    originX:"center", originY:"center",
    textAlign:"center",
    splitByGrapheme:true,
  });

  const fs = fitFontSimple(tb.text || "", rectW, rectH);
  tb.set({ fontSize: fs });

  tb.clipPath = new fabric.Rect({
    left: 0, top: 0,
    originX:"center", originY:"center",
    width: w, height: h,
    absolutePositioned: false
  });
}

/* ---------- site ---------- */
function computeScale(){
  const usableW = canvas.getWidth() - PAD_LEFT - PAD_RIGHT;
  const usableH = canvas.getHeight() - PAD_TOP - PAD_BOTTOM;
  return Math.max(0.0001, Math.min(usableW / siteW, usableH / siteH));
}
function redrawSiteOnly(){
  canvas.getObjects().forEach(o=>{ if(o.ppType==="SITE") canvas.remove(o); });
  scale = computeScale();
  siteRect = new fabric.Rect({
    left: PAD_LEFT, top: PAD_TOP,
    width: siteW * scale, height: siteH * scale,
    fill: "rgba(200,200,200,0.08)",
    stroke: "rgba(180,180,180,0.95)",
    strokeWidth: 3,
    selectable:false, evented:false, hasControls:false, hasBorders:false, hoverCursor:"default"
  });
  siteRect.ppType = "SITE";
  siteRect.ppMeta = { w_m: siteW, h_m: siteH };
  canvas.add(siteRect);
  canvas.sendToBack(siteRect);
}
function drawSiteFresh(){
  canvas.clear();
  redrawSiteOnly();
  canvas.requestRenderAll();
}

/* ---------- collision + clamp ---------- */
function aabb(obj){
  const r = obj.getBoundingRect(true, true);
  return {x1:r.left, y1:r.top, x2:r.left+r.width, y2:r.top+r.height};
}
function overlap(a,b){ return !(a.x2<=b.x1 || a.x1>=b.x2 || a.y2<=b.y1 || a.y1>=b.y2); }

function clampToSite(obj){
  if(!obj || !obj.ppType) return;
  if(obj.ppType==="REMARK") return;
  const b = siteBounds();
  const r = obj.getBoundingRect(true, true);
  let dx=0, dy=0;
  if(r.left < b.x1) dx = b.x1 - r.left;
  if(r.top < b.y1) dy = b.y1 - r.top;
  if(r.left + r.width > b.x2) dx = b.x2 - (r.left + r.width);
  if(r.top + r.height > b.y2) dy = b.y2 - (r.top + r.height);
  if(dx || dy){ obj.left += dx; obj.top += dy; obj.setCoords(); }
}
function clampToCanvas(obj){
  if(!obj || obj.ppType!=="REMARK") return;
  const b = canvasBounds();
  const r = obj.getBoundingRect(true, true);
  let dx=0, dy=0;
  if(r.left < b.x1) dx = b.x1 - r.left;
  if(r.top < b.y1) dy = b.y1 - r.top;
  if(r.left + r.width > b.x2) dx = b.x2 - (r.left + r.width);
  if(r.top + r.height > b.y2) dy = b.y2 - (r.top + r.height);
  if(dx || dy){ obj.left += dx; obj.top += dy; obj.setCoords(); }
}

function setGroupStroke(group, hex, isError){
  if(!group || !group._objects) return;
  const rect = group._objects[0];
  rect.set({
    stroke: isError ? "rgba(239,68,68,0.95)" : rgba(hex, 0.95),
    strokeWidth: isError ? 3 : 2
  });
}
function validateCollisions(){
  const objs = canvas.getObjects().filter(o => o.ppType && o.ppType!=="SITE");
  const b = siteBounds();

  for(const o of objs){
    if(o.ppType==="REMARK") continue;
    setGroupStroke(o, o.ppMeta.fillHex, false);
  }
  for(const o of objs){
    if(o.ppType==="REMARK") continue;
    const r = aabb(o);
    const out = (r.x1<b.x1 || r.y1<b.y1 || r.x2>b.x2 || r.y2>b.y2);
    if(out) setGroupStroke(o, o.ppMeta.fillHex, true);
  }
  for(let i=0;i<objs.length;i++){
    for(let j=i+1;j<objs.length;j++){
      if(objs[i].ppType==="REMARK" || objs[j].ppType==="REMARK") continue;
      if(overlap(aabb(objs[i]), aabb(objs[j]))){
        setGroupStroke(objs[i], objs[i].ppMeta.fillHex, true);
        setGroupStroke(objs[j], objs[j].ppMeta.fillHex, true);
      }
    }
  }
  canvas.requestRenderAll();
}

/* ---------- object factory ---------- */
function addPlotObject(type, w_m, h_m){
  if(!siteRect) return;

  const style = defaultByType[type] || defaultByType["건물"];
  const w = Math.max(2, w_m) * scale;
  const h = Math.max(2, h_m) * scale;

  const b = siteBounds();
  const cx = (b.x1+b.x2)/2;
  const cy = (b.y1+b.y2)/2;

  const rect = new fabric.Rect({
    left:0, top:0,
    originX:"center", originY:"center",
    width:w, height:h,
    fill: rgba(style.fill, 0.22),
    stroke: rgba(style.fill, 0.95),
    strokeWidth: 2
  });

  const tb = new fabric.Textbox("", {
    left:0, top:0,
    originX:"center", originY:"center",
    textAlign:"center",
    fill:"rgba(11,17,27,0.95)",
    fontSize:18,
    splitByGrapheme:true
  });
  applyTextboxLayout(tb, w, h);

  const group = new fabric.Group([rect, tb], {
    left:cx, top:cy,
    originX:"center", originY:"center",
    angle:0
  });

  group.setControlsVisibility({tl:false,tr:false,bl:false,br:false,ml:false,mr:false,mt:false,mb:false,mtr:true});
  group.lockScalingX = true;
  group.lockScalingY = true;

  group.ppType = type;
  group.ppMeta = { w_m, h_m, fillHex: style.fill, label:"" };

  canvas.add(group);
  canvas.setActiveObject(group);
  clampToSite(group);

  pushUndo();
  saveStateToStorage();
  validateCollisions();
}

/* ---------- remark ---------- */
function addRemark(text){
  const b = siteBounds();
  const cx = (b.x1+b.x2)/2;
  const cy = (b.y1+b.y2)/2;

  const tb = new fabric.Textbox(text || "Remark", {
    left:cx, top:cy,
    originX:"center", originY:"center",
    textAlign:"left",
    fontSize:14,
    fill:"#0b1220",
    width:240
  });
  tb.ppType = "REMARK";
  tb.ppMeta = { label: text || "" };

  canvas.add(tb);
  canvas.setActiveObject(tb);
  clampToCanvas(tb);

  pushUndo();
  saveStateToStorage();
  validateCollisions();
}

/* ---------- events ---------- */
canvas.on("object:moving", e=>{
  const obj = e.target;
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;
  if(obj.ppType==="REMARK") clampToCanvas(obj);
  else clampToSite(obj);
  validateCollisions();
  saveStateToStorage();
});

canvas.on("object:rotating", e=>{
  const obj = e.target;
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;
  obj.setCoords();
  if(obj.ppType!=="REMARK") clampToSite(obj);
  validateCollisions();
  saveStateToStorage();
});

canvas.on("object:scaling", e=>{
  const obj = e.target;
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;
  if(obj.ppType!=="REMARK"){ obj.scaleX=1; obj.scaleY=1; obj.setCoords(); }
  saveStateToStorage();
});

canvas.on("object:modified", ()=>{
  pushUndo();
  saveStateToStorage();
  validateCollisions();
});

/* ---------- modal edit ---------- */
const modalBack = document.getElementById("modalBack");
const colorGrid = document.getElementById("colorGrid");
const labelText = document.getElementById("labelText");
let selColor = "#3b82f6";

function renderPalette(){
  colorGrid.innerHTML = "";
  for(const hex of palette){
    const el = document.createElement("div");
    el.className = "swatch";
    el.style.background = hex;
    el.onclick = ()=>{ selColor = hex; renderPalette(); };
    if(hex === selColor) el.classList.add("sel");
    colorGrid.appendChild(el);
  }
}
function openModalFor(obj){
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;
  modalBack.style.display = "flex";

  if(obj.ppType==="REMARK"){
    selColor = (obj.fill && obj.fill.startsWith("#")) ? obj.fill : "#0b1220";
    labelText.value = obj.text || "";
  }else{
    selColor = (obj.ppMeta && obj.ppMeta.fillHex) ? obj.ppMeta.fillHex : "#3b82f6";
    labelText.value = (obj.ppMeta && obj.ppMeta.label) ? obj.ppMeta.label : "";
  }
  renderPalette();
}
function closeModal(){ modalBack.style.display = "none"; }
document.getElementById("modalClose").onclick = closeModal;

canvas.on("mouse:dblclick", ()=>{
  const obj = canvas.getActiveObject();
  if(obj && obj.ppType && obj.ppType!=="SITE") openModalFor(obj);
});

document.getElementById("applyEdit").onclick = ()=>{
  const obj = canvas.getActiveObject();
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;

  pushUndo();

  if(obj.ppType==="REMARK"){
    obj.set({ fill: selColor, text: labelText.value || "" });
    obj.ppMeta.label = obj.text;
    obj.setCoords();
    clampToCanvas(obj);
  }else{
    obj.ppMeta.fillHex = selColor;
    obj.ppMeta.label = labelText.value || "";

    const rect = obj._objects[0];
    const tb = obj._objects[1];

    rect.set({ fill: rgba(selColor,0.22), stroke: rgba(selColor,0.95), strokeWidth:2 });
    tb.set({ text: obj.ppMeta.label });

    applyTextboxLayout(tb, rect.width, rect.height);
    obj.addWithUpdate();
    obj.setCoords();
    clampToSite(obj);
  }

  saveStateToStorage();
  validateCollisions();
  closeModal();
};

document.getElementById("deleteSel").onclick = ()=>{
  const obj = canvas.getActiveObject();
  if(!obj || !obj.ppType || obj.ppType==="SITE") return;
  pushUndo();
  canvas.remove(obj);
  canvas.discardActiveObject();
  saveStateToStorage();
  validateCollisions();
  closeModal();
};

/* ---------- keys ---------- */
window.addEventListener("keydown", (e)=>{
  if(e.key==="Delete"){
    e.preventDefault();
    const obj = canvas.getActiveObject();
    if(obj && obj.ppType && obj.ppType!=="SITE"){
      pushUndo();
      canvas.remove(obj);
      canvas.discardActiveObject();
      saveStateToStorage();
      validateCollisions();
    }
  }
  if((e.ctrlKey||e.metaKey) && (e.key==="z" || e.key==="Z")){
    e.preventDefault();
    undo();
  }
});

/* ---------- rotation immediate ---------- */
document.querySelectorAll(".rotBtn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    const obj = canvas.getActiveObject();
    if(!obj || !obj.ppType || obj.ppType==="SITE") return;
    const deg = parseInt(btn.dataset.rot || "0", 10);
    if(!deg) return;

    pushUndo();
    obj.rotate((obj.angle||0) + deg);
    obj.setCoords();

    if(obj.ppType==="REMARK") clampToCanvas(obj);
    else clampToSite(obj);

    saveStateToStorage();
    validateCollisions();
  });
});

/* ---------- buttons ---------- */
document.getElementById("applySite").onclick = ()=>{
  const w = parseFloat(document.getElementById("siteW").value || "1");
  const h = parseFloat(document.getElementById("siteH").value || "1");
  siteW = Math.max(1, w);
  siteH = Math.max(1, h);

  redrawSiteOnly();
  canvas.sendToBack(siteRect);

  canvas.getObjects().forEach(o=>{
    if(!o.ppType || o.ppType==="SITE") return;
    if(o.ppType==="REMARK") clampToCanvas(o);
    else clampToSite(o);
  });

  pushUndo();
  saveStateToStorage();
  validateCollisions();
};

document.getElementById("addObj").onclick = ()=>{
  const type = document.getElementById("objType").value || "건물";
  const w = parseFloat(document.getElementById("objW").value || "1");
  const h = parseFloat(document.getElementById("objH").value || "1");
  addPlotObject(type, Math.max(0.2,w), Math.max(0.2,h));
};

document.getElementById("addRemark").onclick = ()=>{
  const txt = document.getElementById("remarkText").value || "Remark";
  addRemark(txt);
};

document.getElementById("resetAll").onclick = ()=>{
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(UNDO_KEY);
  undoStack.length = 0;

  siteW = 500; siteH = 300;
  document.getElementById("siteW").value = 500;
  document.getElementById("siteH").value = 300;

  drawSiteFresh();
  pushUndo();
  saveStateToStorage();
  validateCollisions();
};

/* ---------- PDF export (Korean safe): rasterize canvas including title above site ---------- */
document.getElementById("savePDF").onclick = ()=>{
  const title = (document.querySelector(".projectTitle").textContent || "").trim();

  const b = siteBounds();
  const titleX = (b.x1 + b.x2)/2;
  const titleY = b.y1 - 28;

  const titleObj = new fabric.Text(title, {
    left:titleX, top:titleY,
    originX:"center", originY:"bottom",
    fontSize:22, fontWeight:"bold",
    fill:"#0b1220",
    selectable:false, evented:false
  });
  titleObj.ppType = "TEMP_TITLE";
  canvas.add(titleObj);
  canvas.bringToFront(titleObj);
  canvas.requestRenderAll();

  const dataURL = canvas.toDataURL({ format:"png", multiplier:2 });
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ orientation:"landscape", unit:"pt", format:"a4" });

  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();

  const img = new Image();
  img.onload = ()=>{
    const iw = img.width, ih = img.height;
    const margin = 24;
    const maxW = pageW - margin*2;
    const maxH = pageH - margin*2;
    const r = Math.min(maxW/iw, maxH/ih);
    const dw = iw*r, dh = ih*r;
    const x = (pageW - dw)/2;
    const y = (pageH - dh)/2;
    pdf.addImage(dataURL, "PNG", x, y, dw, dh);
    pdf.save("plotplan.pdf");

    canvas.remove(titleObj);
    canvas.requestRenderAll();
  };
  img.src = dataURL;
};

/* ---------- persistence: save/load objects only ---------- */
function saveStateToStorage(){
  try{
    const snap = canvas.toDatalessJSON(["ppType","ppMeta"]);
    const filtered = {...snap, objects:(snap.objects||[]).filter(o => !(o && o.ppType==="SITE") && !(o && o.ppType==="TEMP_TITLE"))};
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  }catch(e){ console.warn("save err", e); }
}

function fixLoadedObjectsAfterRestore(){
  canvas.getObjects().forEach(o=>{
    if(!o.ppType || o.ppType==="SITE") return;

    if(o.type==="group" && o._objects && o._objects.length>=2){
      o.setControlsVisibility({tl:false,tr:false,bl:false,br:false,ml:false,mr:false,mt:false,mb:false,mtr:true});
      o.lockScalingX = true; o.lockScalingY = true;

      const rect = o._objects[0];
      const tb = o._objects[1];

      rect.set({ originX:"center", originY:"center", left:0, top:0 });
      tb.set({ originX:"center", originY:"center", left:0, top:0, textAlign:"center", splitByGrapheme:true });

      applyTextboxLayout(tb, rect.width, rect.height);
      o.addWithUpdate();
      o.setCoords();
      clampToSite(o);
    }

    if(o.ppType==="REMARK") clampToCanvas(o);
  });
}

function tryRestoreFromStorage(){
  try{
    const raw = localStorage.getItem(STORAGE_KEY);
    if(!raw) return false;
    const json = JSON.parse(raw);

    drawSiteFresh();

    canvas.loadFromJSON(json, ()=>{
      canvas.sendToBack(siteRect);
      fixLoadedObjectsAfterRestore();
      validateCollisions();
      canvas.requestRenderAll();
    });

    try{
      const u = localStorage.getItem(UNDO_KEY);
      if(u){
        const arr = JSON.parse(u);
        if(Array.isArray(arr)){
          undoStack.length = 0;
          arr.slice(-UNDO_LIMIT).forEach(x=>undoStack.push(x));
        }
      }
    }catch(_){}

    return true;
  }catch(e){
    console.warn("restore err", e);
    return false;
  }
}

/* ---------- init ---------- */
drawSiteFresh();
tryRestoreFromStorage();
pushUndo();
saveStateToStorage();
renderPalette();
window.addEventListener("beforeunload", ()=>{ saveStateToStorage(); });
</script>
</body>
</html>
"""

# Insert project title (safe replace)
HTML = HTML_template.replace("__PROJECT_TITLE__", project_title.replace("\n", " "))

st.markdown("### Plot Plan (Streamlit에서 실행되는 웹앱)")
components.html(HTML, height=920, scrolling=True)
