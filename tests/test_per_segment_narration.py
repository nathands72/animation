"""
Test script for per-segment narration functionality.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.video_assembler import VideoAssemblyAgent
from utils.helpers import get_temp_path
import tempfile

def test_audio_duration_extraction():
    """Test audio duration helper method."""
    print("\n=== Test 1: Audio Duration Extraction ===")
    
    agent = VideoAssemblyAgent()
    
    # Use existing narration file if available
    audio_file = Path('temp/audio/narration.mp3')
    if audio_file.exists():
        duration = agent._get_audio_duration(audio_file)
        print(f"[PASS] Audio duration: {duration:.2f}s")
        assert duration > 0, "Duration should be positive"
        print("[PASS] Test passed")
    else:
        print("[SKIP] No existing audio file to test, skipping")

def test_segment_narration_generation():
    """Test segment narration generation."""
    print("\n=== Test 2: Segment Narration Generation ===")
    
    agent = VideoAssemblyAgent()
    
    # Test segment with narration
    segment = {
        'scene_number': 1,
        'narration': 'Once upon a time, there was a brave little rabbit who loved to explore.',
        'dialogue': None
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = agent.generate_segment_narration(segment, 0, Path(tmpdir))
        
        if result:
            print(f"[PASS] Audio generated: {result['audio_path']}")
            print(f"[PASS] Duration: {result['duration']:.2f}s")
            assert result['audio_path'].exists(), "Audio file should exist"
            assert result['duration'] > 0, "Duration should be positive"
            print("[PASS] Test passed")
        else:
            print("[FAIL] No narration generated")
            raise AssertionError("Narration generation failed")

def test_segment_without_narration():
    """Test segment without narration."""
    print("\n=== Test 3: Segment Without Narration ===")
    
    agent = VideoAssemblyAgent()
    
    # Test segment without narration
    segment = {
        'scene_number': 2,
        'narration': None,
        'dialogue': None
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = agent.generate_segment_narration(segment, 1, Path(tmpdir))
        
        if result is None:
            print("[PASS] Correctly returned None for segment without narration")
            print("[PASS] Test passed")
        else:
            print("[FAIL] Should have returned None")
            raise AssertionError("Should not generate narration for empty segment")

def test_segment_with_dialogue():
    """Test segment with dialogue instead of narration."""
    print("\n=== Test 4: Segment With Dialogue ===")
    
    agent = VideoAssemblyAgent()
    
    # Test segment with dialogue
    segment = {
        'scene_number': 3,
        'narration': None,
        'dialogue': 'Hello, my friend! How are you today?'
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = agent.generate_segment_narration(segment, 2, Path(tmpdir))
        
        if result:
            print(f"[PASS] Audio generated from dialogue: {result['audio_path']}")
            print(f"[PASS] Duration: {result['duration']:.2f}s")
            assert result['audio_path'].exists(), "Audio file should exist"
            assert result['duration'] > 0, "Duration should be positive"
            print("[PASS] Test passed")
        else:
            print("[FAIL] Failed to generate narration from dialogue")
            raise AssertionError("Dialogue narration generation failed")

if __name__ == "__main__":
    print("=" * 60)
    print("Per-Segment Narration Test Suite")
    print("=" * 60)
    
    try:
        test_audio_duration_extraction()
        test_segment_narration_generation()
        test_segment_without_narration()
        test_segment_with_dialogue()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
