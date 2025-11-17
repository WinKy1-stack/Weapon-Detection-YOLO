import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO

def evaluate_model():
    # Point to the newly trained optimized stable model
    MODEL_PATH = r"runs/detect/weapons_yolov8_optimized_stable/weights/best.pt"
    DATA_PATH = r"dataset/data.yaml"
    SAVE_DIR = r"runs/evaluate/"
    os.makedirs(SAVE_DIR, exist_ok=True)

    print("📊 Đang đánh giá mô hình...")
    model = YOLO(MODEL_PATH)
    metrics = model.val(data=DATA_PATH, split='val', save_json=False, verbose=True)

    # Lấy thông tin lớp
    class_names = list(model.names.values())

    # YOLOv8 >= 8.3 lưu kết quả từng lớp trong metrics.box.map50_classwise (mAP50)
    # Precision/Recall per-class lấy qua metrics.box.ap_per_class() (nếu có)
    box = getattr(metrics, "box", None)

    if not box or not hasattr(box, "map50_classwise"):
        print("⚠️ Phiên bản YOLO hiện tại không trả về dữ liệu chi tiết từng lớp.")
        print("→ Đang tạo bảng tổng quát từ metrics.results_dict thay thế...")
        df = pd.DataFrame([metrics.results_dict])
        df.to_csv(os.path.join(SAVE_DIR, "summary_metrics.csv"), index=False)
        print(df)
        return

    # Trích xuất giá trị chi tiết từng lớp
    mAP50 = box.map50_classwise if hasattr(box, "map50_classwise") else []
    mAP5095 = box.map_classwise if hasattr(box, "map_classwise") else []
    precision = box.precision if hasattr(box, "precision") else []
    recall = box.recall if hasattr(box, "recall") else []

    # Tạo bảng dữ liệu
    data = []
    for i, cls in enumerate(class_names):
        row = {
            "Class": cls,
            "Precision": precision[i] if i < len(precision) else None,
            "Recall": recall[i] if i < len(recall) else None,
            "mAP50": mAP50[i] if i < len(mAP50) else None,
            "mAP50-95": mAP5095[i] if i < len(mAP5095) else None,
        }
        data.append(row)

    df = pd.DataFrame(data)
    print("\n✅ BẢNG ĐÁNH GIÁ CHI TIẾT:")
    print(df.to_string(index=False))

    # Lưu CSV
    csv_path = os.path.join(SAVE_DIR, "detailed_metrics.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n📁 Đã lưu bảng chi tiết tại: {csv_path}")

    # Vẽ biểu đồ
    plt.figure(figsize=(10, 6))
    df_melted = df.melt(id_vars=["Class"], value_vars=["Precision", "Recall", "mAP50"],
                        var_name="Metric", value_name="Score")
    sns.barplot(x="Class", y="Score", hue="Metric", data=df_melted)
    plt.title("📊 Hiệu năng mô hình YOLOv8 theo từng lớp")
    plt.ylim(0, 1)
    plt.ylabel("Giá trị (0–1)")
    plt.xlabel("Tên lớp đối tượng")
    plt.legend(loc='lower right')
    plt.tight_layout()

    plot_path = os.path.join(SAVE_DIR, "classwise_performance.png")
    plt.savefig(plot_path, dpi=300)
    plt.show()
    print(f"\n📈 Biểu đồ chi tiết từng lớp đã lưu tại: {plot_path}")

if __name__ == "__main__":
    evaluate_model()
