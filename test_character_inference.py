"""Quick test script to verify character inference tool."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.character_inference_tool import CharacterInferenceTool

# Set up logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test data
character_names = ["Max", "Phoenix"]
script_segments = [
    {
        "scene_number": 5,
        "description": "Leo encounters Max, the mischievous monkey, who tries to trick Leo into giving him the feather.",
        "characters": ["Leo", "Max"],
        "dialogue": "Oh, what a shiny feather! Give it to me, and I will show you a shortcut to the Phoenix.",
    },
    {
        "scene_number": 8,
        "description": "Leo explains his journey and returns the feather to the Phoenix.",
        "characters": ["Leo", "Phoenix"],
        "dialogue": "I wanted to take the shortcut, but I knew it wasn't the right thing to do. This is your feather, and it was my duty to return it.",
    },
    {
        "scene_number": 9,
        "description": "The Phoenix grants Leo a wish as a token of gratitude.",
        "characters": ["Leo", "Phoenix"],
        "dialogue": "Thank you, Leo. I grant you a wish. Choose wisely!",
    }
]

story_context = {
    "theme": "honesty",
    "setting": "magical forest",
    "moral_lesson": "Honesty is the best policy, even when it's hard"
}

# Test the tool
print("Testing CharacterInferenceTool...")
print(f"Characters to infer: {character_names}")
print()

tool = CharacterInferenceTool()
result = tool.infer_characters_from_segments(
    character_names=character_names,
    script_segments=script_segments,
    story_context=story_context
)

print("\n" + "="*60)
print("RESULT:")
print("="*60)
print(result)
