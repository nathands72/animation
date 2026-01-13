"""Test script to verify story segmentation covers the entire story."""

import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_segmentation_coverage():
    """Test that segmentation covers the entire story."""
    from agents.script_segmenter import ScriptSegmentationAgent
    
    logger.info("=" * 60)
    logger.info("TEST: Story Segmentation Coverage")
    logger.info("=" * 60)
    
    # Create a test story
    test_story = """Once upon a time in a magical forest, there lived a brave young lion named Leo. Leo was known throughout the forest for his courage and curiosity. One sunny morning, Leo discovered a mysterious golden acorn hidden beneath an old oak tree.

Leo wanted to keep the acorn for himself, but he knew it belonged to his friend Mia, the wise owl. Mia had been searching for this special acorn for many days. Leo faced a difficult choice: should he keep the treasure or tell the truth?

As Leo thought about what to do, he remembered what his mother had taught him about honesty. Even though it was hard, Leo decided to bring the acorn to Mia. When Mia saw the acorn, her eyes lit up with joy.

"Thank you for being honest, Leo," Mia said warmly. "This acorn has magical powers that can help our entire forest. Because you told the truth, everyone will benefit." Leo felt proud and happy. He learned that honesty is always the best choice, even when it's difficult."""

    # Create test context
    test_context = {
        "theme": "honesty",
        "characters": [
            {"name": "Leo", "type": "lion", "traits": ["brave", "curious"]},
            {"name": "Mia", "type": "owl", "traits": ["wise", "kind"]}
        ],
        "setting": "magical forest",
        "moral_lesson": "Honesty is the best policy, even when it's hard",
        "age_group": "6-8",
        "duration_minutes": 3
    }
    
    # Create segmenter
    segmenter = ScriptSegmentationAgent()
    
    # Segment the story
    logger.info("\\nSegmenting test story...")
    logger.info(f"Story length: {len(test_story.split())} words")
    logger.info(f"Story preview: {test_story[:100]}...")
    
    segments = segmenter.segment(
        story=test_story,
        context=test_context,
        target_duration_minutes=3
    )
    
    # Analyze results
    logger.info(f"\\nGenerated {len(segments)} segments")
    
    # Check each segment
    total_narration_words = 0
    for i, segment in enumerate(segments, 1):
        narration = segment.get("narration", "")
        word_count = len(narration.split())
        total_narration_words += word_count
        
        logger.info(f"\\nSegment {i}:")
        logger.info(f"  Scene number: {segment.get('scene_number')}")
        logger.info(f"  Narration words: {word_count}")
        logger.info(f"  Narration preview: {narration[:80]}...")
        logger.info(f"  Duration: {segment.get('duration_seconds')}s")
    
    # Calculate coverage
    story_words = len(test_story.split())
    coverage_ratio = total_narration_words / story_words
    
    logger.info(f"\\n{'=' * 60}")
    logger.info("COVERAGE ANALYSIS")
    logger.info(f"{'=' * 60}")
    logger.info(f"Original story words: {story_words}")
    logger.info(f"Total narration words: {total_narration_words}")
    logger.info(f"Coverage ratio: {coverage_ratio:.1%}")
    
    # Check if story is complete
    combined_narration = " ".join(seg.get("narration", "") for seg in segments)
    
    # Check first and last sentences
    story_sentences = test_story.split(". ")
    first_sentence = story_sentences[0]
    last_sentence = story_sentences[-1]
    
    has_beginning = first_sentence[:50] in combined_narration
    has_ending = last_sentence[-50:] in combined_narration
    
    logger.info(f"\\nHas story beginning: {has_beginning}")
    logger.info(f"Has story ending: {has_ending}")
    
    if has_beginning and has_ending and coverage_ratio >= 0.85:
        logger.info(f"\\n✅ SUCCESS: Story is completely segmented!")
        logger.info(f"   - Beginning present: {has_beginning}")
        logger.info(f"   - Ending present: {has_ending}")
        logger.info(f"   - Coverage: {coverage_ratio:.1%}")
    else:
        logger.warning(f"\\n⚠️ WARNING: Story may be incomplete!")
        logger.warning(f"   - Beginning present: {has_beginning}")
        logger.warning(f"   - Ending present: {has_ending}")
        logger.warning(f"   - Coverage: {coverage_ratio:.1%}")
        
        if not has_ending:
            logger.warning(f"\\n❌ ISSUE: Story ending is missing!")
            logger.warning(f"Expected ending: ...{last_sentence[-100:]}")
            logger.warning(f"Last segment narration: {segments[-1].get('narration', '')[-100:]}")


def main():
    """Run the test."""
    logger.info("Testing Story Segmentation Coverage")
    logger.info("=" * 60)
    
    try:
        test_segmentation_coverage()
        
    except Exception as e:
        logger.error(f"\\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
