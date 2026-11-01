"""Supported tool_execute_after extension: geometry only, never page contents."""
import json
from pathlib import Path
from PIL import Image
from helpers.extension import Extension

class VisualGeometry(Extension):
    async def execute(self, response=None, tool_name="", **kwargs):
        if response is None or tool_name.split(":")[0] != "browser":
            return
        try:
            data = json.loads(response.message)
            path = data.get("path", "")
            if not data.get("vision_load") or not path:
                return
            resolved = Path(path).resolve()
            if not str(resolved).startswith("/a0/usr/chats/"):
                return
            with Image.open(resolved) as image:
                width, height = image.size
            data["visual_geometry"] = {
                "screenshot_width_pixels": width,
                "screenshot_height_pixels": height,
                "instructions": "Load this screenshot with vision_load. For viewport screenshots, origin (0,0) is top-left of page content, NOT browser chrome. Browser click x/y use viewport CSS pixels; default device scale is 1. Estimate target center as fractions of this complete image width/height and convert to native pixels; do not use normalized 0..1000 coordinates or invent offsets. If model image preprocessing rescales the image, preserve the fractions and map back to the native dimensions above. Use full_page=false for clicking. Identify target from pixels, click once, then take and load a NEW screenshot to verify actual state change. After a miss re-estimate from fresh pixels; never repeat an unchanged failed coordinate. Stop after at most 4 clicks without success and report the limitation honestly. Never infer success from a click return alone."
            }
            response.message = json.dumps(data)
        except (ValueError, TypeError, OSError):
            return
