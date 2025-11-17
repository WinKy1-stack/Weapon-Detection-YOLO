import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports like `src.*` work when running main.py
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference import WeaponDetector
from src.training import WeaponTrainer
from src.utils import setup_logger

logger = setup_logger('main')

def train_command(args):
    """Handle training commands"""
    trainer = WeaponTrainer(model_name=args.model)
    
    if args.validate_only:
        trainer.validate()
    else:
        custom_config = {
            'epochs': args.epochs,
            'batch_size': args.batch
        }
        trainer.train(custom_config, args.name)

def detect_command(args):
    """Handle detection commands"""
    detector = WeaponDetector(model_path=args.model)
    
    if args.mode == 'image':
        detector.detect_image(args.source, args.save_dir)
    elif args.mode == 'video':
        detector.detect_video(args.source, args.save_dir)
    elif args.mode == 'realtime':
        detector.realtime_detect(save_dir=args.save_dir)

def main():
    parser = argparse.ArgumentParser(description='Weapon Detection CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Training parser
    train_parser = subparsers.add_parser('train', help='Train the model')
    train_parser.add_argument('--model', default='yolov8m.pt', help='Base model to use')
    train_parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    train_parser.add_argument('--batch', type=int, default=8, help='Batch size')
    train_parser.add_argument('--name', default='weapons_yolov8', help='Experiment name')
    train_parser.add_argument('--validate-only', action='store_true', help='Only run validation')
    
    # Detection parser
    detect_parser = subparsers.add_parser('detect', help='Run detection')
    detect_parser.add_argument('--source', help='Path to image/video file')
    detect_parser.add_argument('--model', help='Path to custom model')
    detect_parser.add_argument('--save-dir', help='Directory to save results')
    detect_parser.add_argument('--mode', choices=['image', 'video', 'realtime'],
                             default='image', help='Detection mode')
    
    args = parser.parse_args()

    # If no command provided, default to running detection on the test images
    if args.command is None:
        logger.info("No command provided — defaulting to detection on dataset/test/images")
        # Build default args for detect
        class D:
            pass

        dargs = D()
        dargs.model = None
        dargs.save_dir = None
        dargs.mode = 'image'
        # point to test images directory — detect_image will accept a folder path
        dargs.source = str(PROJECT_ROOT / 'dataset' / 'test' / 'images')
        detect_command(dargs)
        return

    if args.command == 'train':
        train_command(args)
    elif args.command == 'detect':
        detect_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()