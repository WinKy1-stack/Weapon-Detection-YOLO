import argparse
from src.inference.detector import WeaponDetector
from src.utils.logging import setup_logger
from pathlib import Path

logger = setup_logger('detect_script')

def main():
    parser = argparse.ArgumentParser(description='Detect weapons in images/videos')
    parser.add_argument('--source', required=True, help='Path to image or video file')
    parser.add_argument('--model', help='Path to custom model')
    parser.add_argument('--save-dir', help='Directory to save results')
    parser.add_argument('--mode', choices=['image', 'video', 'realtime'], 
                       default='image', help='Detection mode')
    args = parser.parse_args()
    
    try:
        detector = WeaponDetector(model_path=args.model)
        
        if args.mode == 'image':
            annotated_img, detections = detector.detect_image(
                args.source, 
                args.save_dir
            )
            logger.info(f"Detected {len(detections)} objects")
            
        elif args.mode == 'video':
            save_path = detector.detect_video(
                args.source, 
                args.save_dir
            )
            logger.info(f"Processed video saved to: {save_path}")
            
        elif args.mode == 'realtime':
            detector.realtime_detect()
            
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()