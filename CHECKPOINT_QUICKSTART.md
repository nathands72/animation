# Checkpoint Feature - Quick Reference

## CLI Commands

### Run with Checkpointing (Default)
```bash
python main.py --input story.json --workflow-id my-video-001
```

### Resume from Latest Checkpoint
```bash
python main.py --workflow-id my-video-001 --resume
```

### Resume from Specific Step
```bash
python main.py --workflow-id my-video-001 --resume-from-step story_generator
```

Available steps:
- `context_analyzer`
- `web_researcher`
- `story_generator`
- `script_segmenter`
- `character_designer`
- `video_assembler`

### List Checkpoints
```bash
python main.py --workflow-id my-video-001 --list-checkpoints
```

### Resume from Specific Checkpoint File
```bash
python main.py --checkpoint-path temp/checkpoints/my-video-001/checkpoint_story_generator_20231213_143125.json
```

### Disable Checkpointing
```bash
python main.py --input story.json --no-checkpoint
```

## Checkpoint Locations

All checkpoints are saved to:
```
temp/checkpoints/{workflow_id}/
```

Each step creates:
- **Checkpoint file**: `checkpoint_{step_name}_{timestamp}.json`
- **Intermediate outputs**: Numbered files (01_*, 02_*, etc.)
- **Latest symlink**: `latest_checkpoint.json`

## Testing

Run the test script to verify checkpoint functionality:
```bash
python test_checkpoints.py
```

## Documentation

See [docs/checkpointing.md](file:///c:/cursor/animation/docs/checkpointing.md) for complete documentation.
