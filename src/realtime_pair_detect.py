from ultralytics import YOLO
import cv2
import numpy as np

def detect_weapon_person_pair(source=0):
    # --- Load models ---
    person_model = YOLO("yolov8n.pt")  # model pretrained trên COCO (chứa class 'person')
    # Load the updated weapon model (optimized stable)
    weapon_model = YOLO(r"runs/detect/weapons_yolov8_optimized_stable/weights/best.pt")  # model của bạn

    # --- Lấy danh sách class vũ khí ---
    weapon_classes = weapon_model.names  # dict: {0: 'pistol', 1: 'knife', ...}

    # --- Mở nguồn video hoặc webcam ---
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("❌ Không thể mở video hoặc camera.")
        return

    print("📹 Hệ thống phát hiện người cầm vũ khí đang hoạt động...")
    print("👉 Nhấn Q để thoát.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- Dự đoán người & vũ khí ---
        persons = person_model.predict(frame, conf=0.6, classes=[0], verbose=False)[0]
        weapons = weapon_model.predict(frame, conf=0.6, verbose=False)[0]

        annotated = frame.copy()

        # --- Danh sách người & vũ khí ---
        person_boxes = [box.xyxy[0].cpu().numpy() for box in persons.boxes]
        weapon_boxes = [(box.xyxy[0].cpu().numpy(), int(box.cls), float(box.conf)) for box in weapons.boxes]

        # --- Vẽ khung người ---
        for pbox in person_boxes:
            x1, y1, x2, y2 = map(int, pbox)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, "Person", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # --- Vẽ khung vũ khí & gán cho người gần nhất ---
        for wbox, wcls, conf in weapon_boxes:
            wx1, wy1, wx2, wy2 = map(int, wbox)
            wcx, wcy = (wx1 + wx2) // 2, (wy1 + wy2) // 2
            weapon_name = weapon_classes[wcls]  # Lấy tên class từ model
            conf_text = f"{weapon_name} ({conf:.2f})"

            # Vẽ khung đỏ cho vũ khí
            cv2.rectangle(annotated, (wx1, wy1), (wx2, wy2), (0, 0, 255), 2)
            cv2.circle(annotated, (wcx, wcy), 5, (0, 0, 255), -1)

            # Tìm người gần nhất
            nearest_person = None
            min_dist = float('inf')

            for pbox in person_boxes:
                px1, py1, px2, py2 = map(int, pbox)
                pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
                dist = np.sqrt((wcx - pcx)**2 + (wcy - pcy)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_person = (px1, py1, px2, py2)

            # Nếu vũ khí gần người (trong ngưỡng 150px)
            if nearest_person and min_dist < 150:
                px1, py1, px2, py2 = nearest_person
                pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
                cv2.line(annotated, (wcx, wcy), (pcx, pcy), (255, 255, 0), 2)
                cv2.putText(annotated, f"Held by Person - {conf_text}",
                            (wx1, wy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (255, 255, 0), 2)
            else:
                cv2.putText(annotated, f"{conf_text} (No Owner)",
                            (wx1, wy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 0, 255), 2)

        # --- Hiển thị kết quả ---
        cv2.imshow("Weapon–Person Pair Detection", annotated)

        # Thoát khi nhấn Q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Webcam mặc định hoặc video
    # detect_weapon_person_pair("dataset/test/video1.mp4")
    detect_weapon_person_pair(0)
