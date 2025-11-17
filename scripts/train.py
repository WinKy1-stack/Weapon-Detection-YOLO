import argparse
from src.training.trainer import WeaponTrainer
from src.utils.logging import setup_logger

logger = setup_logger('train_script')

def main():
    parser = argparse.ArgumentParser(description='Train weapon detection model')
    parser.add_argument('--model', default='yolov8m.pt', help='Base model to use')
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--name', default='weapons_yolov8', help='Experiment name')
    args = parser.parse_args()
    
    try:
        trainer = WeaponTrainer(model_name=args.model)
        custom_config = {
            'epochs': args.epochs,
            'batch_size': args.batch_size
        }
        
        best_model = trainer.train(custom_config, args.name)
        logger.info(f"Training completed successfully. Best model: {best_model}")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()