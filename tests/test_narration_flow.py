"""Test script to verify hybrid narration flow implementation."""

import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_story_splitting():
    """Test the story splitting functionality."""
    from agents.video_assembler import VideoAssemblyAgent
    
    logger.info("=" * 60)
    logger.info("TEST 1: Story Splitting")
    logger.info("=" * 60)
    
    assembler = VideoAssemblyAgent()
    
    # Sample story
    story = """Once upon a time, there was a little rabbit named Rosie. She loved to hop around the meadow. One day, she found a shiny acorn. Rosie wanted to keep it all to herself. But then she saw her friend Timmy the squirrel looking sad. Timmy had lost his acorn collection. Rosie thought about it carefully. She decided to share her acorn with Timmy. Timmy was so happy and grateful. Rosie learned that sharing brings more joy than keeping things to yourself."""
    
    # Test splitting into different segment counts
    for num_segments in [3, 5, 8]:
        logger.info(f"\nSplitting into {num_segments} segments:")
        chunks = assembler._split_story_into_segments(story, num_segments)
        
        logger.info(f"  Created {len(chunks)} chunks")
        
        # Verify all chunks
        for i, chunk in enumerate(chunks, 1):
            word_count = len(chunk.split())
            logger.info(f"  Segment {i}: {word_count} words - {chunk[:50]}...")
        
        # Verify coverage
        combined = " ".join(chunks)
        story_words = set(story.lower().split())
        combined_words = set(combined.lower().split())
        coverage = len(story_words & combined_words) / len(story_words)
        
        logger.info(f"  Coverage: {coverage:.1%}")
        assert coverage >= 0.95, f"Coverage too low: {coverage:.1%}"
    
    logger.info("\n✅ Story splitting test PASSED")


def test_hybrid_narration_selection():
    """Test the hybrid narration selection logic."""
    from agents.video_assembler import VideoAssemblyAgent
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Hybrid Narration Selection")
    logger.info("=" * 60)
    
    assembler = VideoAssemblyAgent()
    
    # Test cases
    test_cases = [
        {
            "name": "Substantial segment narration",
            "segment": {"narration": "This is a long narration with more than twenty words to ensure it passes the threshold for segment narration usage."},
            "story_chunk": "This is the story chunk fallback.",
            "expected_source": "segment"
        },
        {
            "name": "Short segment narration",
            "segment": {"narration": "Too short."},
            "story_chunk": "This is the story chunk fallback with sufficient length.",
            "expected_source": "story_chunk"
        },
        {
            "name": "No segment narration",
            "segment": {},
            "story_chunk": "This is the story chunk fallback when no segment narration exists.",
            "expected_source": "story_chunk"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n  Test case {i}: {test_case['name']}")
        
        result = assembler._get_segment_narration_text(
            segment=test_case["segment"],
            story_chunk=test_case["story_chunk"],
            segment_index=i-1
        )
        
        if test_case["expected_source"] == "segment":
            expected = test_case["segment"]["narration"]
        else:
            expected = test_case["story_chunk"]
        
        logger.info(f"    Expected: {expected[:50]}...")
        logger.info(f"    Got: {result[:50]}...")
        
        assert result == expected, f"Mismatch in test case {i}"
        logger.info(f"    ✅ Correct source selected")
    
    logger.info("\n✅ Hybrid narration selection test PASSED")


def test_script_segmentation_validation():
    """Test the script segmentation story coverage validation."""
    from agents.script_segmenter import ScriptSegmentationAgent
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Script Segmentation Validation")
    logger.info("=" * 60)
    
    segmenter = ScriptSegmentationAgent()
    
    story = "The quick brown fox jumps over the lazy dog. This is a test story."
    
    # Test case 1: Good coverage
    good_segments = [
        {"narration": "The quick brown fox jumps over the lazy dog."},
        {"narration": "This is a test story."}
    ]
    
    logger.info("\n  Test case 1: Good coverage (should pass)")
    result = segmenter._validate_story_coverage(good_segments, story)
    logger.info(f"    Result: {result}")
    assert result == True, "Good coverage should pass validation"
    logger.info("    ✅ PASSED")
    
    # Test case 2: Poor coverage
    poor_segments = [
        {"narration": "Something completely different."},
        {"narration": "Not related at all."}
    ]
    
    logger.info("\n  Test case 2: Poor coverage (should fail)")
    result = segmenter._validate_story_coverage(poor_segments, story)
    logger.info(f"    Result: {result}")
    assert result == False, "Poor coverage should fail validation"
    logger.info("    ✅ PASSED")
    
    # Test case 3: No narration
    empty_segments = [
        {"narration": ""},
        {"narration": ""}
    ]
    
    logger.info("\n  Test case 3: No narration (should fail)")
    result = segmenter._validate_story_coverage(empty_segments, story)
    logger.info(f"    Result: {result}")
    assert result == False, "Empty narration should fail validation"
    logger.info("    ✅ PASSED")
    
    logger.info("\n✅ Script segmentation validation test PASSED")


def main():
    """Run all tests."""
    logger.info("Starting Hybrid Narration Flow Tests")
    logger.info("=" * 60)
    
    try:
        test_story_splitting()
        test_hybrid_narration_selection()
        test_script_segmentation_validation()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("\nThe hybrid narration flow implementation is working correctly:")
        logger.info("  ✅ Story splitting distributes full story across segments")
        logger.info("  ✅ Hybrid selection prefers segment narration when substantial")
        logger.info("  ✅ Validation ensures 85%+ story coverage")
        logger.info("\nYou can now run the full video generation pipeline with confidence")
        logger.info("that the complete story will be narrated across all segments.")
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    main()
