# Checkpoint and Resume Feature

## Overview

The moral video workflow now supports automatic checkpointing and resume functionality. This allows you to:
- **Save progress** automatically after each workflow step
- **Resume execution** from the last completed step if interrupted
- **Restart from specific steps** to iterate on later stages
- **Recover from errors** without losing expensive API calls

## Quick Start

### Normal Execution with Auto-Checkpointing

```bash
python main.py --input story.json --workflow-id my-video-001
```

Checkpoints are automatically saved after each step to `temp/checkpoints/my-video-001/`.

### Resume from Latest Checkpoint

If your workflow was interrupted or failed:

```bash
python main.py --workflow-id my-video-001 --resume
```

This loads the latest checkpoint and continues from the next step.

### Resume from Specific Step

To restart from a particular step (e.g., to regenerate the video with different settings):

```bash
python main.py --workflow-id my-video-001 --resume-from-step video_assembler
```

Available steps:
- `context_analyzer`
- `web_researcher`
- `story_generator`
- `script_segmenter`
- `character_designer`
- `video_assembler`

### List Available Checkpoints

```bash
python main.py --workflow-id my-video-001 --list-checkpoints
```

Output:
```
Available checkpoints for workflow 'my-video-001':
============================================================
1. context_analyzer      - 2023-12-13 14:30:22
2. web_researcher        - 2023-12-13 14:30:45
3. story_generator       - 2023-12-13 14:31:25
4. script_segmenter      - 2023-12-13 14:31:56
```

### Disable Checkpointing

For faster execution without checkpoints:

```bash
python main.py --input story.json --no-checkpoint
```

## Checkpoint File Structure

```
temp/checkpoints/
└── {workflow_id}/
    ├── checkpoint_context_analyzer_20231213_143022.json
    ├── checkpoint_web_researcher_20231213_143045.json
    ├── checkpoint_story_generator_20231213_143125.json
    ├── checkpoint_script_segmenter_20231213_143156.json
    ├── checkpoint_character_designer_20231213_143445.json
    ├── checkpoint_video_assembler_20231213_143612.json
    ├── latest_checkpoint.json
    ├── 01_validated_context.json
    ├── 01_search_queries.json
    ├── 02_research_results.json
    ├── 02_research_summary.txt
    ├── 03_story.txt
    ├── 03_story_metadata.json
    ├── 04_script_segments.json
    ├── 05_character_descriptions.json
    ├── 05_scene_image_paths.json
    └── 06_final_output.json
```

### Checkpoint Files

- **checkpoint_*.json**: Full workflow state at each step
- **latest_checkpoint.json**: Copy of the most recent checkpoint
- **##_*.json/txt**: Intermediate outputs from each step (human-readable)

## Error Recovery Scenarios

### Scenario 1: API Timeout During Story Generation

```
Step 1: ✓ Context Analyzer (checkpoint saved)
Step 2: ✓ Web Researcher (checkpoint saved)
Step 3: ✗ Story Generator (API timeout)
```

**Recovery:**
```bash
python main.py --workflow-id abc123 --resume-from-step story_generator
```

This retries step 3 without re-running steps 1-2.

### Scenario 2: User Interruption (Ctrl+C)

```
Step 1: ✓ Context Analyzer (checkpoint saved)
Step 2: ✓ Web Researcher (checkpoint saved)
Step 3: ✓ Story Generator (checkpoint saved)
Step 4: ⚠ Script Segmenter (interrupted mid-execution)
```

**Recovery:**
```bash
python main.py --workflow-id abc123 --resume
```

Automatically continues from step 4.

### Scenario 3: Out of Memory During Video Assembly

```
Steps 1-5: ✓ All completed (checkpoints saved)
Step 6: ✗ Video Assembler (OOM error)
```

**Recovery:**
1. Free up system memory
2. Resume from video assembly:
```bash
python main.py --workflow-id abc123 --resume-from-step video_assembler
```

This retries video assembly without regenerating expensive images.

## Configuration

Edit `config.py` to customize checkpoint behavior:

```python
class WorkflowConfig:
    # ...
    enable_auto_checkpoint: bool = True  # Enable/disable auto-checkpointing
    checkpoint_retention_count: int = 10  # Number of checkpoints to keep
```

## Advanced Usage

### Resume from Specific Checkpoint File

```bash
python main.py --checkpoint-path temp/checkpoints/my-video-001/checkpoint_story_generator_20231213_143125.json
```

### Programmatic Access

```python
from utils.checkpoint_manager import CheckpointManager, load_checkpoint

# Load a checkpoint
manager = CheckpointManager(Path("temp/checkpoints"))
state, step_name = manager.load_checkpoint(checkpoint_path)

# List checkpoints
checkpoints = manager.list_checkpoints("my-workflow-id")
for cp in checkpoints:
    print(f"{cp['step_name']}: {cp['timestamp']}")
```

## Troubleshooting

### "No checkpoints found for workflow"

**Cause:** Workflow ID doesn't match or checkpoints were deleted.

**Solution:** 
- Verify workflow ID: `python main.py --workflow-id YOUR_ID --list-checkpoints`
- Check `temp/checkpoints/` directory exists

### "Checkpoint file not found"

**Cause:** Checkpoint file was moved or deleted.

**Solution:**
- Use `--list-checkpoints` to see available checkpoints
- Resume from latest: `--resume` instead of `--checkpoint-path`

### Workflow re-runs all steps even when resuming

**Note:** This is expected behavior. LangGraph's linear workflow will re-execute all nodes, but each node checks if its output already exists in the resumed state. Future versions may implement conditional edges for true step-skipping.

## Best Practices

1. **Always use --workflow-id** for production runs to enable checkpoint tracking
2. **Keep checkpoints** until workflow completes successfully
3. **Monitor disk space** - checkpoints can accumulate (auto-cleanup keeps last 10)
4. **Use meaningful workflow IDs** like `video-honesty-v1` instead of random UUIDs
5. **Resume from specific steps** when iterating on later stages (e.g., video assembly)

## Performance Impact

- **Checkpoint save time**: ~50-200ms per step (minimal)
- **Disk space**: ~1-5MB per checkpoint (varies with story length)
- **Resume overhead**: ~100-500ms to load checkpoint

Checkpointing adds negligible overhead compared to API calls (which take seconds to minutes).
