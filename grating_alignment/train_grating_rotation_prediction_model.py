import torch
import torch.nn as nn
import torch.optim as optim
import logging
import os
import argparse
import time
from tqdm import tqdm
from typing import Tuple, List
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from EstimateGratingRotation import GratingRotationPredictorWithFftResnet18
from RotatedGartingImageDataset import RotatedGartingImageDataset
from shared.LoggingFormatter import ColoredLoggingFormatter

def _create_data_loaders(
    root_dir: str,
    excel_file_path: str,
    batch_size: int = 32,
    train_split: float = 0.8,
    num_workers: int = 4,
    logger: logging.Logger = None
) -> Tuple[DataLoader, DataLoader]:
    """Create train and validation data loaders"""
    
    # Create dataset
    full_dataset = RotatedGartingImageDataset(
        root_dir=root_dir,
        excel_file_path=excel_file_path,
        logger=logger
    )
    
    # Split dataset
    total_size = len(full_dataset)
    train_size = int(train_split * total_size)
    val_size = total_size - train_size

        # Define transforms
    train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels = 3),  # Convert grayscale to RGB
        transforms.RandomAffine(degrees = 10, translate = (0.1, 0.1), scale = (0.9, 1.1), shear = 10),
        transforms.RandomEqualize(p = 0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        transforms.RandomRotation(degrees = 10)
    ])

    test_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels = 3),  # Convert grayscale to RGB
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    train_dataset: torch.utils.data.subset.Subset
    test_dataset: torch.utils.data.subset.Subset
    train_dataset, test_dataset = random_split(
        full_dataset, 
        [train_size, val_size],
        generator = torch.Generator().manual_seed(42)
    )
    train_dataset.dataset.transform = train_transform
    test_dataset.dataset.transform = test_transform
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size = batch_size, shuffle = True, num_workers = num_workers, pin_memory = True, persistent_workers = True)
    test_loader = DataLoader(test_dataset, batch_size = batch_size, shuffle = False, num_workers = num_workers, pin_memory = True, persistent_workers = True)
    
    return train_loader, test_loader

def train_epoch(model: nn.Module, train_loader: DataLoader, optimizer: optim.Optimizer, criterion: nn.Module, device: str | torch.device) -> float:
    """Train the model for one epoch"""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for images, grating_info in tqdm(train_loader, desc = "Training", leave = False):
        images:torch.FloatTensor = images.to(device)
        targets:torch.FloatTensor = grating_info.grating_side_rotation_deg.reshape(-1, 1).to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs: torch.FloatTensor = model(images).to(dtype = torch.float32)
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
    total_rmse = 0.0
    total_mae = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for images, grating_info in tqdm(val_loader, desc = "Evaluating", leave = False):
            images = images.to(device)
            
            # Extract target rotation angle
            targets = grating_info.grating_side_rotation_deg.reshape(-1, 1).to(device)
            
            # Forward pass
            outputs = model(images).to(dtype = torch.float32)
            loss:torch.FloatTensor = criterion(outputs, targets)
            
            # Calculate metrics
            rmse = torch.sqrt(torch.mean((outputs - targets) ** 2))
            mae = torch.mean(torch.abs(outputs - targets))
            
            total_loss += loss.item()
            total_rmse += rmse.item()
            total_mae += mae.item()
            num_batches += 1
    
    avg_loss = total_loss / num_batches
    avg_rmse = total_rmse / num_batches
    avg_mae = total_mae / num_batches
    
    return avg_loss, avg_rmse, avg_mae

def _save_checkpoint(model: nn.Module, optimizer: optim.Optimizer, epoch: int, loss: float, rmse:float, filepath: str, device: torch.device, logger: logging.Logger) -> bool:
    """Save model checkpoint"""
    
    model.to("cpu")
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'rmse': rmse,
    }
    save_success = False
    try:
        torch.save(checkpoint, filepath)
        save_success = True
    except IOError as e:
        model.to(device)
        logger.error("Failed to save checkpoint: %s", e)

    model.to(device)
    return save_success

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
        console_handler.setFormatter(ColoredLoggingFormatter.instance())
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
    parser.add_argument("--num_epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Fraction of data to use for training (rest for validation)")
    
    # Logging and output arguments
    parser.add_argument("--log_dir", type=str, default="logs", help="Directory to save logs")
    parser.add_argument("--model_save_dir", type=str, default="models", help="Directory to save model checkpoints")
    parser.add_argument("--log_level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    parser.add_argument("--log_to_file", action="store_true", help="Enable logging to file")
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine device
    device: torch.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    
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
    
    main_logger.debug("Starting training with arguments: %s", vars(args))
    main_logger.info("Using device: %s", device)
    
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
    train_loader, val_loader = _create_data_loaders(args.root_dir, args.excel_file_path, args.batch_size, args.train_ratio, 4, data_loader_logger)
    
    data_loader_logger.info("Train samples: %d", len(train_loader.dataset))
    data_loader_logger.info("Validation samples: %d", len(val_loader.dataset))
    
    # Load model or create new one
    model = GratingRotationPredictorWithFftResnet18()
    model = model.to(device)
    
    # Create optimizer and criterion
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
    criterion = nn.MSELoss()
    
    
    # Training variables
    best_val_loss = float('inf')
    best_val_rmse = float('inf')
    best_val_mae = float('inf')
    train_losses:List[float] = []
    val_losses:List[float] = []
    
    # Start training
    main_logger.info("Starting training...")
    start_time = time.time()
    
    for epoch in range(1, args.num_epochs + 1):
        # Training
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        train_losses.append(train_loss)
        
        # Validation (every epoch)
        val_loss, val_rmse, val_mae = evaluate_model(model, val_loader, criterion, device)
        val_losses.append(val_loss)
        
        # Log results
        main_logger.info("Epoch %d/%d - Train Loss: %.4f, Val Loss: %.4f, Val RMSE: %.4f, Val MAE: %.4f",
                       epoch, args.num_epochs, train_loss, val_loss, val_rmse, val_mae)
        
        
        # Save best model when validation loss improves
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_rmse = val_rmse
            best_val_mae = val_mae
            main_logger.info("Saving new best model with validation loss: %.4f, validation RMSE: %.4f, validation MAE: %.4f", val_loss, val_rmse, val_mae)
            _save_checkpoint(model, optimizer, epoch, val_loss, val_rmse, os.path.join(args.model_save_dir, "best_model.pth"), device, main_logger)
        
    # Training summary
    total_time = time.time() - start_time
    main_logger.info("Training completed!")
    main_logger.info("Total training time: %.2f seconds", total_time)
    main_logger.info("Best validation loss: %.4f", best_val_loss)
    main_logger.info("Best validation RMSE: %.4f", best_val_rmse)
    main_logger.info("Best validation MAE: %.4f", best_val_mae)
    main_logger.info("Final model saved in : %s. Please use git-lfs to track and push this file to the repository.", args.model_save_dir)

if __name__ == "__main__":
    main()