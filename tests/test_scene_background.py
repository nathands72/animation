"""Test script to verify scene_background field generation."""

import logging
from agents.script_segmenter import ScriptSegmentationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scene_background_field():
    """Test that scene_background field is generated with detailed descriptions."""
    
    # Sample story
    story = """Once upon a time in a magical forest, there lived a brave young lion named Leo. Leo was known throughout the forest for his courage and kindness.

One sunny morning, Leo discovered a mysterious golden acorn hidden beneath an old oak tree. The acorn sparkled with an enchanting glow.

Leo wanted to keep the acorn for himself, but he knew it belonged to his friend Mia, a wise old owl who had been searching for it. Leo faced a difficult choice: should he keep the treasure or tell the truth?

After much thought, Leo decided to return the acorn to Mia. When Mia saw the acorn, her eyes lit up with joy. "Thank you for being honest, Leo," Mia said warmly.

Leo felt proud and happy. He learned that honesty is always the best choice, even when it's difficult."""

    # Context
    context = {
        "theme": "honesty",
        "characters": [
            {"name": "Leo", "type": "lion", "traits": ["brave", "kind"]},
            {"name": "Mia", "type": "owl", "traits": ["wise", "friendly"]}
        ],
        "setting": "magical forest",
        "moral_lesson": "Honesty is the best policy",
        "age_group": "5-8 years"
    }
    
    # Create agent and segment
    agent = ScriptSegmentationAgent()
    segments = agent.segment(story, context, target_duration_minutes=3)
    
    logger.info(f"\n{'='*60}")
    logger.info("SCENE BACKGROUND FIELD VERIFICATION")
    logger.info(f"{'='*60}")
    
    # Check each segment for scene_background field
    all_have_background = True
    for i, segment in enumerate(segments, 1):
        scene_bg = segment.get("scene_background", "")
        setting = segment.get("setting", "")
        
        logger.info(f"\nSegment {i}:")
        logger.info(f"  Setting: {setting}")
        logger.info(f"  Scene Background: {scene_bg}")
        
        if not scene_bg:
            logger.warning(f"  ⚠️  Missing scene_background field!")
            all_have_background = False
        else:
            # Count sentences (rough estimate)
            sentence_count = scene_bg.count('.') + scene_bg.count('!') + scene_bg.count('?')
            word_count = len(scene_bg.split())
            logger.info(f"  Background length: {word_count} words, ~{sentence_count} sentences")
            
            if word_count < 20:
                logger.warning(f"  ⚠️  Scene background seems too brief (< 20 words)")
    
    logger.info(f"\n{'='*60}")
    if all_have_background:
        logger.info("✅ SUCCESS: All segments have scene_background field!")
    else:
        logger.error("❌ FAILURE: Some segments missing scene_background field")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    test_scene_background_field()
