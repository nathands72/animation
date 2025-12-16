"""Checkpoint manager for workflow state persistence and recovery."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages workflow checkpoints for state persistence and recovery."""
    
    def __init__(self, checkpoint_dir: Path, retention_count: int = 10):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Base directory for checkpoints
            retention_count: Maximum number of checkpoints to retain per workflow
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.retention_count = retention_count
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(
        self,
        state: Dict[str, Any],
        step_name: str,
        workflow_id: str
    ) -> Path:
        """
        Save workflow state checkpoint.
        
        Args:
            state: Current workflow state dictionary
            step_name: Name of the completed step
            workflow_id: Unique workflow identifier
            
        Returns:
            Path to saved checkpoint file
        """
        try:
            # Create workflow-specific checkpoint directory
            workflow_checkpoint_dir = self.checkpoint_dir / workflow_id
            workflow_checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate checkpoint filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_filename = f"checkpoint_{step_name}_{timestamp}.json"
            checkpoint_path = workflow_checkpoint_dir / checkpoint_filename
            
            # Prepare checkpoint data
            checkpoint_data = {
                "workflow_id": workflow_id,
                "step_name": step_name,
                "timestamp": datetime.now().isoformat(),
                "last_completed_step": step_name,
                "state": self._serialize_state(state)
            }
            
            # Save checkpoint
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            
            # Update latest checkpoint symlink/copy
            latest_path = workflow_checkpoint_dir / "latest_checkpoint.json"
            shutil.copy2(checkpoint_path, latest_path)
            
            # Clean up old checkpoints
            self._cleanup_old_checkpoints(workflow_id)
            
            return checkpoint_path
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            raise
    
    def load_checkpoint(self, checkpoint_path: Path) -> Tuple[Dict[str, Any], str]:
        """
        Load workflow state from checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
            
        Returns:
            Tuple of (state_dict, step_name)
            
        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            ValueError: If checkpoint data is invalid
        """
        try:
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
            
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # Validate checkpoint structure
            required_fields = ["workflow_id", "step_name", "state"]
            for field in required_fields:
                if field not in checkpoint_data:
                    raise ValueError(f"Invalid checkpoint: missing field '{field}'")
            
            state = self._deserialize_state(checkpoint_data["state"])
            step_name = checkpoint_data["step_name"]
            
            logger.info(f"Checkpoint loaded: {checkpoint_path} (step: {step_name})")
            
            return state, step_name
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            raise
    
    def list_checkpoints(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of checkpoint info dictionaries with keys:
            - path: Path to checkpoint file
            - step_name: Step name
            - timestamp: ISO timestamp
            - file_size: File size in bytes
        """
        workflow_checkpoint_dir = self.checkpoint_dir / workflow_id
        
        if not workflow_checkpoint_dir.exists():
            logger.warning(f"No checkpoints found for workflow: {workflow_id}")
            return []
        
        checkpoints = []
        
        # Find all checkpoint files (excluding latest_checkpoint.json)
        for checkpoint_file in sorted(workflow_checkpoint_dir.glob("checkpoint_*.json")):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    "path": checkpoint_file,
                    "step_name": data.get("step_name", "unknown"),
                    "timestamp": data.get("timestamp", ""),
                    "file_size": checkpoint_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"Error reading checkpoint {checkpoint_file}: {e}")
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return checkpoints
    
    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Path]:
        """
        Get path to latest checkpoint for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Path to latest checkpoint, or None if no checkpoints exist
        """
        workflow_checkpoint_dir = self.checkpoint_dir / workflow_id
        latest_path = workflow_checkpoint_dir / "latest_checkpoint.json"
        
        if latest_path.exists():
            return latest_path
        
        # Fallback: find most recent checkpoint file
        checkpoints = self.list_checkpoints(workflow_id)
        if checkpoints:
            return checkpoints[0]["path"]
        
        return None
    
    def get_checkpoint_for_step(
        self,
        workflow_id: str,
        step_name: str
    ) -> Optional[Path]:
        """
        Get most recent checkpoint for a specific step.
        
        Args:
            workflow_id: Workflow identifier
            step_name: Step name to find checkpoint for
            
        Returns:
            Path to checkpoint, or None if not found
        """
        checkpoints = self.list_checkpoints(workflow_id)
        
        # Find most recent checkpoint for this step
        for checkpoint in checkpoints:
            if checkpoint["step_name"] == step_name:
                return checkpoint["path"]
        
        return None
    
    def _cleanup_old_checkpoints(self, workflow_id: str):
        """
        Remove old checkpoints beyond retention limit.
        
        Args:
            workflow_id: Workflow identifier
        """
        checkpoints = self.list_checkpoints(workflow_id)
        
        # Keep only the most recent N checkpoints
        if len(checkpoints) > self.retention_count:
            for checkpoint in checkpoints[self.retention_count:]:
                try:
                    checkpoint["path"].unlink()
                    logger.debug(f"Removed old checkpoint: {checkpoint['path']}")
                except Exception as e:
                    logger.warning(f"Error removing checkpoint: {e}")
    
    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize state for JSON storage.
        
        Args:
            state: State dictionary
            
        Returns:
            JSON-serializable state dictionary
        """
        # Create a copy to avoid modifying original
        serialized = {}
        
        for key, value in state.items():
            # Handle Path objects
            if isinstance(value, Path):
                serialized[key] = str(value)
            # Handle lists of Paths
            elif isinstance(value, list) and value and isinstance(value[0], Path):
                serialized[key] = [str(p) for p in value]
            # Keep everything else as-is (JSON-serializable types)
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize state from JSON storage.
        
        Args:
            state: Serialized state dictionary
            
        Returns:
            Deserialized state dictionary
        """
        # State is already in the correct format from JSON
        # Path objects will be reconstructed when needed by the workflow
        return state


# Module-level convenience functions

def save_checkpoint(
    state: Dict[str, Any],
    step_name: str,
    checkpoint_dir: Path,
    workflow_id: Optional[str] = None,
    retention_count: int = 10
) -> Path:
    """
    Save workflow checkpoint (convenience function).
    
    Args:
        state: Current workflow state
        step_name: Name of completed step
        checkpoint_dir: Checkpoint directory
        workflow_id: Workflow ID (extracted from state if not provided)
        retention_count: Number of checkpoints to retain
        
    Returns:
        Path to saved checkpoint
    """
    if workflow_id is None:
        workflow_id = state.get("workflow_id", "default")
    
    manager = CheckpointManager(checkpoint_dir, retention_count)
    return manager.save_checkpoint(state, step_name, workflow_id)


def load_checkpoint(checkpoint_path: Path) -> Tuple[Dict[str, Any], str]:
    """
    Load workflow checkpoint (convenience function).
    
    Args:
        checkpoint_path: Path to checkpoint file
        
    Returns:
        Tuple of (state_dict, step_name)
    """
    # Use a temporary manager just for loading
    manager = CheckpointManager(checkpoint_path.parent.parent)
    return manager.load_checkpoint(checkpoint_path)


def list_checkpoints(workflow_id: str, checkpoint_dir: Path) -> List[Dict[str, Any]]:
    """
    List checkpoints for workflow (convenience function).
    
    Args:
        workflow_id: Workflow identifier
        checkpoint_dir: Checkpoint directory
        
    Returns:
        List of checkpoint info dictionaries
    """
    manager = CheckpointManager(checkpoint_dir)
    return manager.list_checkpoints(workflow_id)


def get_latest_checkpoint(workflow_id: str, checkpoint_dir: Path) -> Optional[Path]:
    """
    Get latest checkpoint for workflow (convenience function).
    
    Args:
        workflow_id: Workflow identifier
        checkpoint_dir: Checkpoint directory
        
    Returns:
        Path to latest checkpoint or None
    """
    manager = CheckpointManager(checkpoint_dir)
    return manager.get_latest_checkpoint(workflow_id)
