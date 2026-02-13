"""
GPU acceleration utilities for document processing and embeddings.
"""
import os
from typing import Optional
from loguru import logger


class GPUManager:
    """Manage GPU acceleration settings."""
    
    def __init__(self, enabled: bool = False, device_id: int = 0, memory_fraction: float = 0.8):
        """
        Initialize GPU manager.
        
        Args:
            enabled: Whether GPU acceleration is enabled
            device_id: GPU device ID to use
            memory_fraction: Fraction of GPU memory to use (0.1-1.0)
        """
        self.enabled = enabled
        self.device_id = device_id
        self.memory_fraction = memory_fraction
        self.available = False
        self.device_name = None
        
        if self.enabled:
            self._initialize_gpu()
    
    def _initialize_gpu(self):
        """Initialize GPU if available."""
        try:
            import torch
            
            if torch.cuda.is_available():
                self.available = True
                self.device_name = torch.cuda.get_device_name(self.device_id)
                
                # Set device
                torch.cuda.set_device(self.device_id)
                
                # Set memory fraction
                if hasattr(torch.cuda, 'set_per_process_memory_fraction'):
                    torch.cuda.set_per_process_memory_fraction(
                        self.memory_fraction,
                        device=self.device_id
                    )
                
                logger.info(f"GPU acceleration enabled: {self.device_name}")
                logger.info(f"GPU device ID: {self.device_id}")
                logger.info(f"GPU memory fraction: {self.memory_fraction}")
            else:
                logger.warning("GPU acceleration requested but CUDA is not available")
                self.enabled = False
                
        except ImportError:
            logger.warning("PyTorch not installed. GPU acceleration disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Error initializing GPU: {str(e)}")
            self.enabled = False
    
    def get_device(self) -> str:
        """
        Get the device string for PyTorch.
        
        Returns:
            Device string ('cuda:0', 'cuda:1', or 'cpu')
        """
        if self.enabled and self.available:
            return f"cuda:{self.device_id}"
        return "cpu"
    
    def get_info(self) -> dict:
        """
        Get GPU information.
        
        Returns:
            Dictionary with GPU information
        """
        info = {
            "enabled": self.enabled,
            "available": self.available,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "memory_fraction": self.memory_fraction
        }
        
        if self.available:
            try:
                import torch
                info["cuda_version"] = torch.version.cuda
                info["pytorch_version"] = torch.__version__
                info["device_count"] = torch.cuda.device_count()
                
                # Get memory info
                memory_allocated = torch.cuda.memory_allocated(self.device_id)
                memory_reserved = torch.cuda.memory_reserved(self.device_id)
                total_memory = torch.cuda.get_device_properties(self.device_id).total_memory
                
                info["memory"] = {
                    "allocated_mb": memory_allocated / (1024 ** 2),
                    "reserved_mb": memory_reserved / (1024 ** 2),
                    "total_mb": total_memory / (1024 ** 2)
                }
            except Exception as e:
                logger.error(f"Error getting GPU info: {str(e)}")
        
        return info
    
    def clear_cache(self):
        """Clear GPU cache."""
        if self.enabled and self.available:
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared")
            except Exception as e:
                logger.error(f"Error clearing GPU cache: {str(e)}")
    
    @staticmethod
    def list_available_gpus() -> list:
        """
        List all available GPUs.
        
        Returns:
            List of GPU information dictionaries
        """
        gpus = []
        try:
            import torch
            
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    gpus.append({
                        "id": i,
                        "name": props.name,
                        "total_memory_mb": props.total_memory / (1024 ** 2),
                        "compute_capability": f"{props.major}.{props.minor}"
                    })
        except ImportError:
            logger.warning("PyTorch not installed. Cannot list GPUs.")
        except Exception as e:
            logger.error(f"Error listing GPUs: {str(e)}")
        
        return gpus


def configure_gpu_for_docling(gpu_manager: GPUManager) -> dict:
    """
    Configure GPU settings for Docling document processing.
    
    Args:
        gpu_manager: GPUManager instance
        
    Returns:
        Configuration dictionary for Docling
    """
    config = {
        "use_gpu": gpu_manager.enabled and gpu_manager.available,
        "device": gpu_manager.get_device()
    }
    
    if config["use_gpu"]:
        logger.info("Docling will use GPU acceleration")
    else:
        logger.info("Docling will use CPU")
    
    return config


def configure_gpu_for_embeddings(gpu_manager: GPUManager) -> dict:
    """
    Configure GPU settings for embedding generation.
    
    Args:
        gpu_manager: GPUManager instance
        
    Returns:
        Configuration dictionary for embeddings
    """
    config = {
        "use_gpu": gpu_manager.enabled and gpu_manager.available,
        "device": gpu_manager.get_device(),
        "batch_size": 32 if gpu_manager.enabled else 8  # Larger batches with GPU
    }
    
    if config["use_gpu"]:
        logger.info("Embeddings will use GPU acceleration")
    else:
        logger.info("Embeddings will use CPU")
    
    return config


# Environment variable helpers

def get_gpu_config_from_env() -> dict:
    """
    Get GPU configuration from environment variables.
    
    Returns:
        Dictionary with GPU configuration
    """
    return {
        "enabled": os.getenv("GPU_ENABLED", "false").lower() == "true",
        "device_id": int(os.getenv("GPU_DEVICE_ID", "0")),
        "memory_fraction": float(os.getenv("GPU_MEMORY_FRACTION", "0.8"))
    }

# Made with Bob
