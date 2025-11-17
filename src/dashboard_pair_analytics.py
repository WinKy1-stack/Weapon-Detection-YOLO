import streamlit as st
import pandas as pd
import plotly.express as px
import cv2
import tempfile
import os
import sys
import csv
import numpy as np
from datetime import datetime
import io
from ultralytics import YOLO

# Add project root to path to allow imports to work from any directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.alert_system.alert_manager import trigger_alert, start_alert_worker
from src.database.mongo_client import get_recent_alerts


# ================== CẤU HÌNH CHUNG ==================
st.set_page_config(page_title="Weapon–Person Detection & Analytics", layout="wide")
st.title("🧍🔫 Weapon–Person Detection & Analytics Dashboard")

# --- Đường dẫn log ---
LOG_DIR = "runs/realtime_logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pair_detections_log.csv")

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Datetime", "Weapon_Class", "Confidence", "Distance_to_Person", "Status"])

# ----------------- Log tail helper & sidebar viewer -----------------
def read_last_lines(path, n=100):
    """Read last n lines from a potentially large file efficiently."""
    try:
        with open(path, "rb") as f:
            # Seek to end and read blocks backwards
            avg_line_length = 100
            to_read = n * avg_line_length
            try:
                f.seek(-to_read, os.SEEK_END)
            except OSError:
                f.seek(0)
            data = f.read().decode(errors="replace")
    except FileNotFoundError:
        return "(no log file yet)"

    lines = data.splitlines()
    return "\n".join(lines[-n:])

# Sidebar controls for quick log inspection
with st.sidebar.expander("Logs / Live tail", expanded=False):
    show_logs = st.checkbox("Show recent log lines", value=True)
    log_lines = st.slider("Lines to show", min_value=10, max_value=500, value=50, step=10)
    auto_refresh = st.checkbox("Auto refresh", value=False)
    refresh_interval = st.slider("Refresh interval (s)", min_value=1, max_value=10, value=3)
    if show_logs:
        lines_text = read_last_lines(LOG_FILE, log_lines)
        st.text_area("Recent logs", value=lines_text, height=300)
        if auto_refresh:
            import time
            time.sleep(refresh_interval)
            st.experimental_rerun()

# -------------------------------------------------------------------

# --- Load model ---
person_model = YOLO("yolov8n.pt")
# Load optimized stable weapon model
weapon_model = YOLO(r"runs/detect/weapons_yolov8_optimized_stable/weights/best.pt")
weapon_classes = weapon_model.names

# Ensure alert worker thread is started for this Streamlit session
try:
    start_alert_worker()
except Exception as e:
    print(f"[ALERT WORKER START ERROR] {e}")

# ================== CHỌN TAB ==================
tab1, tab2, tab3 = st.tabs(["🎥 Realtime Detection", "📊 Analytics Dashboard", "🚨 Alerts Dashboard"])


# ================== TAB 1 - REALTIME DETECTION ==================
with tab1:
    st.header("🎥 Weapon–Person Pair Detection")

    source_option = st.sidebar.radio("Nguồn đầu vào:", ["Webcam", "Upload Video"])
    if source_option == "Upload Video":
        uploaded = st.sidebar.file_uploader("Tải video (.mp4, .avi)", type=["mp4", "avi"])
        if uploaded:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded.read())
            source = tfile.name
        else:
            source = None
    else:
        source = 0  # webcam

    if st.sidebar.button("▶ Bắt đầu phát hiện"):
        if source is None:
            st.warning("⚠️ Vui lòng tải video trước khi bắt đầu.")
        else:
            stframe = st.empty()
            # Container for realtime log table (displayed below the video)
            log_table = st.empty()

            # Read header from the CSV log so we can parse tail lines into a DataFrame
            try:
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as hf:
                    header_line = hf.readline().strip()
            except Exception:
                header_line = None

            cap = cv2.VideoCapture(source)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Dự đoán
                persons = person_model.predict(frame, conf=0.6, classes=[0], verbose=False)[0]
                weapons = weapon_model.predict(frame, conf=0.6, verbose=False)[0]
                annotated = frame.copy()

                person_boxes = [box.xyxy[0].cpu().numpy() for box in persons.boxes]
                weapon_boxes = [(box.xyxy[0].cpu().numpy(), int(box.cls), float(box.conf)) for box in weapons.boxes]

                # Vẽ người
                for pbox in person_boxes:
                    x1, y1, x2, y2 = map(int, pbox)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Vẽ vũ khí và liên kết
                for wbox, wcls, conf in weapon_boxes:
                    wx1, wy1, wx2, wy2 = map(int, wbox)
                    wcx, wcy = (wx1 + wx2) // 2, (wy1 + wy2) // 2
                    weapon_name = weapon_classes[wcls]
                    conf_text = f"{weapon_name} ({conf:.2f})"

                    cv2.rectangle(annotated, (wx1, wy1), (wx2, wy2), (0, 0, 255), 2)
                    cv2.circle(annotated, (wcx, wcy), 5, (0, 0, 255), -1)

                    nearest_person = None
                    min_dist = float("inf")
                    for pbox in person_boxes:
                        px1, py1, px2, py2 = map(int, pbox)
                        pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
                        dist = np.sqrt((wcx - pcx) ** 2 + (wcy - pcy) ** 2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_person = (px1, py1, px2, py2)

                    status = "No Owner"
                    if nearest_person and min_dist < 150:
                        px1, py1, px2, py2 = nearest_person
                        pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
                        cv2.line(annotated, (wcx, wcy), (pcx, pcy), (255, 255, 0), 2)
                        status = "Held by Person"
                        # --- Trigger alert system ---
                    try:
                        trigger_alert(frame, weapon_name, conf, min_dist / 100, status)
                    except Exception as e:
                        print(f"[ALERT ERROR] {e}")
                        cv2.putText(
                            annotated,
                            f"Held by Person - {conf_text}",
                            (wx1, wy1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 0),
                            2,
                        )
                    else:
                        cv2.putText(
                            annotated,
                            f"{conf_text} (No Owner)",
                            (wx1, wy1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2,
                        )

                    # Ghi log
                    with open(LOG_FILE, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            weapon_name,
                            round(conf, 2),
                            round(min_dist, 1),
                            status
                        ])

                # Update the displayed video frame
                stframe.image(annotated, channels="BGR", use_container_width=True)

                # ------------------ Realtime log table (below video) ------------------
                # Determine how many lines to show (fall back to 50 if sidebar control missing)
                try:
                    lines_to_display = log_lines
                except Exception:
                    lines_to_display = 50

                if header_line:
                    try:
                        lines_text = read_last_lines(LOG_FILE, lines_to_display)
                        if lines_text and lines_text != "(no log file yet)":
                            csv_text = header_line + "\n" + lines_text
                            df_tail = pd.read_csv(io.StringIO(csv_text))
                            # Display the most recent rows in a scrolling table container
                            log_table.dataframe(df_tail.tail(lines_to_display), use_container_width=True)
                        else:
                            log_table.text("No log entries yet")
                    except Exception as e:
                        # Keep the UI resilient: show error text if parsing fails
                        log_table.text(f"Error reading log: {e}")
                else:
                    log_table.text("Log header not found.")
                # ---------------------------------------------------------------------
            cap.release()

# ================== TAB 2 - ANALYTICS DASHBOARD ==================
with tab2:
    st.header("📊 Weapon Detection Analytics")

    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE)
        except pd.errors.ParserError:
            df = pd.read_csv(LOG_FILE, on_bad_lines="skip")

        if not df.empty:
            # --- Tổng quan ---
            st.subheader("📈 Thống kê tổng quan")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tổng số phát hiện", len(df))
            with col2:
                held_count = len(df[df["Status"] == "Held by Person"])
                st.metric("Người cầm vũ khí", held_count)
            with col3:
                no_owner_count = len(df[df["Status"] == "No Owner"])
                st.metric("Vũ khí không người cầm", no_owner_count)

            # --- Biểu đồ ---
            st.subheader("🔍 Phân tích chi tiết")
            col1, col2 = st.columns(2)

            with col1:
                fig1 = px.bar(df, x="Weapon_Class", color="Status", title="Số lần phát hiện theo loại vũ khí")
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                fig2 = px.pie(df, names="Status", title="Tỷ lệ người cầm vs không cầm")
                st.plotly_chart(fig2, use_container_width=True)

            # --- Biểu đồ theo thời gian ---
            df["Datetime"] = pd.to_datetime(df["Datetime"])
            df["Minute"] = df["Datetime"].dt.strftime("%H:%M")

            fig3 = px.line(df.groupby("Minute").size().reset_index(name="Detections"),
                           x="Minute", y="Detections",
                           title="Lượt phát hiện theo thời gian (phút)")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("📂 Chưa có dữ liệu log nào để phân tích.")
    else:
        st.warning("⚠️ File log chưa tồn tại. Hãy chạy phát hiện realtime trước.")
# ================== TAB 3 - ALERTS DASHBOARD ==================
with tab3:
    st.header("🚨 Alerts Monitoring Dashboard")

    try:
        alerts = get_recent_alerts(limit=50)
        if alerts:
            df_alerts = pd.DataFrame(alerts)
            st.subheader("📋 Danh sách cảnh báo gần nhất")
            st.dataframe(df_alerts[["timestamp", "weapon_class", "status", "confidence", "danger_level"]])

            st.subheader("📊 Thống kê cảnh báo")
            fig_pie = px.pie(df_alerts, names="danger_level", title="Tỷ lệ các mức độ nguy hiểm")
            st.plotly_chart(fig_pie, use_container_width=True)

            fig_bar = px.bar(df_alerts, x="weapon_class", color="danger_level",
                             title="Phân bố cảnh báo theo loại vũ khí")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("⚡ Chưa có cảnh báo nào được ghi nhận.")
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu cảnh báo: {e}")