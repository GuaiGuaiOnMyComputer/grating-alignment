import torch
import torch.nn as nn
import torch.optim as optim
import logging
import os
import argparse
import time
from pathlib import Path
from typing import Tuple
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from EstimateGratingRotation import GratingRotationPredictorWithFftResnet18
from RotatedGartingImageDataset import RotatedGartingImageDataset
from shared.LoggingFormatter import ColoredLoggingFormatter

def create_data_loaders(
    root_dir: str,
    excel_file_path: str,
    batch_size: int = 32,
    train_split: float = 0.8,
    num_workers: int = 4,
    logger: logging.Logger = None
) -> Tuple[DataLoader, DataLoader]:
    """Create train and validation data loaders"""
    
    # Define transforms
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create dataset
    full_dataset = RotatedGartingImageDataset(
        root_dir=root_dir,
        excel_file_path=excel_file_path,
        transform=transform,
        logger=logger
    )
    
    # Split dataset
    total_size = len(full_dataset)
    train_size = int(train_split * total_size)
    val_size = total_size - train_size
    
    train_dataset, val_dataset = random_split(
        full_dataset, 
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader

def train_epoch(model: nn.Module, train_loader: DataLoader, optimizer: optim.Optimizer, criterion: nn.Module, device: str | torch.device) -> float:
    """Train the model for one epoch"""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, (images, grating_info) in enumerate(train_loader):
        images = images.to(device)
        
        # Extract target rotation angle
        targets = torch.tensor([info.grating_side_rotation_deg for info in grating_info], 
                              dtype=torch.float32, device=device).unsqueeze(1)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, targets)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / num_batches

def evaluate_model(model: nn.Module, val_loader: DataLoader, criterion: nn.Module, device: str | torch.device) -> Tuple[float, float, float]:
    """Evaluate the model on validation set"""
    model.eval()
    total_loss = 0.0
    total_mse = 0.0
    total_mae = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for images, grating_info in val_loader:
            images = images.to(device)
            
            # Extract target rotation angle
            targets = torch.tensor([info.grating_side_rotation_deg for info in grating_info], 
                                  dtype=torch.float32, device=device).unsqueeze(1)
            
            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, targets)
            
            # Calculate metrics
            mse = torch.mean((outputs - targets) ** 2)
            mae = torch.mean(torch.abs(outputs - targets))
            
            total_loss += loss.item()
            total_mse += mse.item()
            total_mae += mae.item()
            num_batches += 1
    
    avg_loss = total_loss / num_batches
    avg_mse = total_mse / num_batches
    avg_mae = total_mae / num_batches
    
    return avg_loss, avg_mse, avg_mae

def save_checkpoint(model: nn.Module, optimizer: optim.Optimizer, epoch: int, loss: float, filepath: str, args: argparse.Namespace = None):
    """Save model checkpoint"""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'args': vars(args) if args else None
    }
    torch.save(checkpoint, filepath)

def load_checkpoint(filepath: str, model: nn.Module, optimizer: optim.Optimizer = None, device: str = 'cpu'):
    """Load model checkpoint"""
    checkpoint = torch.load(filepath, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    if optimizer and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return checkpoint.get('epoch', 0), checkpoint.get('loss', 0.0)

def setup_tensorboard(log_dir: str):
    """Setup TensorBoard logging"""
    try:
        from torch.utils.tensorboard import SummaryWriter
        return SummaryWriter(log_dir)
    except ImportError:
        print("Warning: TensorBoard not available. Install with: pip install tensorboard")
        return None

def setup_logging(logger_name:str, log_dir: str, default_level: int = logging.INFO, log_to_file: bool = False, log_to_console: bool = True) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create log directory
    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
    
    # Setup logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(default_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    if log_to_file:
        formatter = ColoredLoggingFormatter.instance()
        file_handler = logging.FileHandler(os.path.join(log_dir, 'training.log'))
        file_handler.setLevel(default_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Create console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(default_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Train GratingRotationPredictorWithFftResnet18 model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    parser.add_argument("--root_dir", type=str, default="rotated-grating-images-topview/images", help="Root directory containing the images")
    parser.add_argument("--excel_file_path", type=str, default="rotated-grating-images-topview/images-and-grating-rotation.ods", help="Path to the Excel file containing image metadata")
    parser.add_argument("--image_extension", type=str, default="png", help="Image file extension")
    
    # Training arguments
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=1e-4, help="Learning rate for optimizer")
    parser.add_argument("--num_epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--patience", type=int, default=10, help="Patience for early stopping")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Fraction of data to use for training (rest for validation)")
    
    # Logging and output arguments
    parser.add_argument("--log_dir", type=str, default="logs", help="Directory to save logs")
    parser.add_argument("--model_save_dir", type=str, default="models", help="Directory to save model checkpoints")
    parser.add_argument("--log_level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    parser.add_argument("--log_to_file", action="store_true", help="Enable logging to file")
    
    # TensorBoard arguments
    parser.add_argument("--tensorboard_dir", type=str, default=None, help="Directory for TensorBoard logs (default: {log_dir}/tensorboard)")
    
    # Resume training arguments
    parser.add_argument("--resume_from", type=str, default=None, help="Path to model checkpoint to resume training from")
    
    # Validation arguments
    parser.add_argument("--val_frequency", type=int, default=1, help="Frequency of validation (every N epochs)")
    parser.add_argument("--save_frequency", type=int, default=10, help="Frequency of saving model checkpoints (every N epochs)")
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Setup TensorBoard directory
    if args.tensorboard_dir is None:
        tensorboard_dir = os.path.join(args.log_dir, "tensorboard")
    else:
        tensorboard_dir = args.tensorboard_dir
    
    # Convert log level string to logging constant
    log_level = getattr(logging, args.log_level.upper())
    
    # Setup logging
    main_logger: logging.Logger = setup_logging(
        logger_name = "MainLogger",
        log_dir = args.log_dir,
        default_level = log_level,
        log_to_file = False,
        log_to_console = True
    )
    
    main_logger.info(f"Starting training with arguments: {vars(args)}")
    main_logger.info(f"Using device: {device}")
    
    # Create directories
    os.makedirs(args.model_save_dir, exist_ok=True)
    
    # Create data loaders
    data_loader_logger: logging.Logger = setup_logging(
        logger_name="RotatedGartingImageDataset",
        log_dir=args.log_dir,
        default_level=log_level,
        log_to_file=False,
        log_to_console= True
    )
    train_loader: torch.utils.data.DataLoader
    val_loader: torch.utils.data.DataLoader
    train_loader, val_loader = create_data_loaders(args.root_dir, args.excel_file_path, args.batch_size, args.train_ratio, 4, data_loader_logger)
    
    data_loader_logger.info(f"Train samples: {len(train_loader.dataset)}")
    data_loader_logger.info(f"Validation samples: {len(val_loader.dataset)}")
    
    # Load model or create new one
    model = GratingRotationPredictorWithFftResnet18()
    model = model.to(device)
    
    # Create optimizer and criterion
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
    criterion = nn.MSELoss()
    
    # Setup TensorBoard logging
    writer = setup_tensorboard(tensorboard_dir)
    
    # Resume from checkpoint if specified
    start_epoch = 1
    if args.resume_from:
        main_logger.info(f"Resuming training from: {args.resume_from}")
        start_epoch, _ = load_checkpoint(args.resume_from, model, optimizer, device)
        start_epoch += 1
        main_logger.info(f"Resuming from epoch: {start_epoch}")
    
    # Training variables
    best_val_loss = float('inf')
    patience_counter = 0
    train_losses = []
    val_losses = []
    
    # Start training
    main_logger.info("Starting training...")
    start_time = time.time()
    
    for epoch in range(start_epoch, args.num_epochs + 1):
        # Training
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        train_losses.append(train_loss)
        
        # Validation
        if epoch % args.val_frequency == 0:
            val_loss, val_mse, val_mae = evaluate_model(model, val_loader, criterion, device)
            val_losses.append(val_loss)
            
            # Log results
            main_logger.info(f"Epoch {epoch}/{args.num_epochs} - "
                           f"Train Loss: {train_loss:.4f}, "
                           f"Val Loss: {val_loss:.4f}, "
                           f"Val MSE: {val_mse:.4f}, "
                           f"Val MAE: {val_mae:.4f}")
            
            # TensorBoard logging
            if writer:
                writer.add_scalar('Loss/Train', train_loss, epoch)
                writer.add_scalar('Loss/Validation', val_loss, epoch)
                writer.add_scalar('Metrics/MSE', val_mse, epoch)
                writer.add_scalar('Metrics/MAE', val_mae, epoch)
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                save_checkpoint(model, optimizer, epoch, val_loss, 
                              os.path.join(args.model_save_dir, "best_model.pth"), args)
                main_logger.info(f"New best model saved with validation loss: {val_loss:.4f}")
            else:
                patience_counter += 1
                
            # Early stopping
            if patience_counter >= args.patience:
                main_logger.info(f"Early stopping triggered after {args.patience} epochs without improvement")
                break
        else:
            # Log training only
            main_logger.info(f"Epoch {epoch}/{args.num_epochs} - Train Loss: {train_loss:.4f}")
            if writer:
                writer.add_scalar('Loss/Train', train_loss, epoch)
        
        # Save checkpoint
        if epoch % args.save_frequency == 0:
            save_checkpoint(model, optimizer, epoch, train_loss, 
                          os.path.join(args.model_save_dir, f"checkpoint_epoch_{epoch}.pth"), args)
            main_logger.info(f"Saved checkpoint at epoch {epoch}")
    
    # Save final model
    save_checkpoint(model, optimizer, epoch, train_loss, os.path.join(args.model_save_dir, "final_model.pth"), args)
    
    # Close TensorBoard writer
    if writer:
        writer.close()
    
    # Training summary
    total_time = time.time() - start_time
    main_logger.info("Training completed!")
    main_logger.info(f"Total training time: {total_time:.2f} seconds")
    main_logger.info(f"Best validation loss: {best_val_loss:.4f}")
    main_logger.info(f"Best model saved in: {args.model_save_dir}")
    main_logger.info(f"TensorBoard logs available in: {tensorboard_dir}")

if __name__ == "__main__":
    main()