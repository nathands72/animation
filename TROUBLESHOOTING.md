# Troubleshooting Guide

## Current Errors and Solutions

### Error 1: gTTS Narration Error
**Error Message:**
```
Error generating gTTS narration: 200 (OK) from TTS API. Probable cause: Unknown
```

**Root Cause:**
- gTTS is receiving HTTP 200 but failing to process the audio data
- This can be caused by network issues, rate limiting, or corrupted installation

**Solutions:**

#### Option A: Reinstall gTTS
```powershell
pip uninstall gtts
pip install gtts --upgrade
```

#### Option B: Switch to ElevenLabs (Recommended for production)
1. Get an API key from https://elevenlabs.io
2. Add to your `.env` file:
   ```
   ELEVENLABS_API_KEY=your_api_key_here
   ```
3. Update your config to use ElevenLabs:
   - The system will automatically use ElevenLabs if the API key is present

#### Option C: Disable narration temporarily
In your workflow input, set:
```python
preferences = {
    "narration": False,
    "music": False
}
```

---

### Error 2: ImageMagick Not Found (CRITICAL)
**Error Message:**
```
Error creating final video: MoviePy Error: creation of None failed because of the following error:
[WinError 2] The system cannot find the file specified.
This error can be due to the fact that ImageMagick is not installed on your computer...
```

**Root Cause:**
MoviePy's `TextClip` functionality requires ImageMagick to render text overlays (used for end cards with moral messages). ImageMagick is NOT a Python package - it's a separate system binary.

**Solution: Install ImageMagick**

#### Step 1: Download ImageMagick
1. Go to: https://imagemagick.org/script/download.php
2. Download the latest Windows binary:
   - Look for `ImageMagick-7.x.x-x-Q16-x64-dll.exe` (recommended)
   - Or `ImageMagick-7.x.x-x-Q16-HDRI-x64-dll.exe` for high dynamic range

#### Step 2: Install ImageMagick
1. Run the installer
2. **IMPORTANT:** During installation, make sure to check these options:
   - ✅ **"Install legacy utilities (e.g., convert)"**
   - ✅ **"Add application directory to your system path"**
3. Complete the installation

#### Step 3: Verify Installation
Open a **new** PowerShell window and run:
```powershell
magick -version
```

You should see output like:
```
Version: ImageMagick 7.x.x-x Q16 x64
Copyright: ...
```

#### Step 4: Configure MoviePy (If needed)
If MoviePy still can't find ImageMagick after installation, you need to manually configure the path.

**Option A: Set Environment Variable**
1. Find your ImageMagick installation path (usually `C:\Program Files\ImageMagick-7.x.x-Q16`)
2. Add to your `.env` file:
   ```
   IMAGEMAGICK_BINARY=C:\Program Files\ImageMagick-7.x.x-Q16\magick.exe
   ```

**Option B: Configure in Python Code**
Add this to your `video_tool.py` after the imports:

```python
import os
from moviepy.config import change_settings

# Set ImageMagick path
imagemagick_path = os.getenv("IMAGEMAGICK_BINARY", r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe")
if os.path.exists(imagemagick_path):
    change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})
```

#### Step 5: Restart Your Application
After installing ImageMagick:
1. Close all PowerShell/terminal windows
2. Restart your Python application
3. Try creating a video again

---

## Alternative Solution: Disable Text Overlays

If you can't install ImageMagick right now, you can temporarily disable the moral message end card:

### Modify `video_tool.py`

Comment out the end card section in the `create_final_video` method (lines 366-387):

```python
# # Add end card with moral message if provided
# if moral_message:
#     logger.info("Adding end card with moral message")
#     
#     # Create end card (3 seconds)
#     end_card_duration = 3.0
#     end_card = self.TextClip(
#         moral_message,
#         fontsize=50,
#         color='white',
#         font='Arial-Bold',
#         stroke_color='black',
#         stroke_width=3,
#         size=(video.w, video.h),
#         method='caption'
#     ).set_duration(end_card_duration).set_position('center')
#     
#     # Add fade in/out to end card
#     end_card = end_card.fx(self.fadein, 0.5).fx(self.fadeout, 0.5)
#     
#     # Concatenate video and end card
#     video = self.concatenate_videoclips([video, end_card], method="compose")
```

This will create videos without the moral message end card, but everything else will work.

---

## Quick Diagnosis Checklist

Run these commands to verify your setup:

```powershell
# Check Python packages
pip list | Select-String "moviepy|gtts|elevenlabs"

# Check ImageMagick
magick -version

# Check ffmpeg (required by MoviePy)
ffmpeg -version

# Check environment variables
Get-ChildItem Env: | Select-String "IMAGEMAGICK|OPENAI|ELEVENLABS"
```

---

## Common Issues

### Issue: "ffmpeg not found"
**Solution:** Install ffmpeg
```powershell
# Using chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### Issue: "Permission denied" when creating videos
**Solution:** Run PowerShell as Administrator or check folder permissions

### Issue: Videos created but no audio
**Solution:** 
1. Check that narration audio file was created in `temp/audio/`
2. Verify ffmpeg supports AAC audio codec
3. Check audio file isn't corrupted

---

## Recommended Setup

For best results, ensure you have:

1. ✅ **ImageMagick** installed with legacy utilities
2. ✅ **ffmpeg** installed and in PATH
3. ✅ **MoviePy** installed: `pip install moviepy`
4. ✅ **gTTS** or **ElevenLabs** for narration
5. ✅ All API keys in `.env` file
6. ✅ Sufficient disk space in `temp/` and `output/` directories
