import io
import re
from PIL import Image

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.lib.storage import read_file

router = APIRouter(tags=["maps"])

_BASEMAP_FILENAMES: dict[str, str] = {
    "boston-seaport":           "36092f0b03a857c6a3403e25b4b7aab3.png",
    "singapore-hollandvillage": "37819e65e09e5547b8a3ceaefba56bb2.png",
    "singapore-onenorth":       "53992ee3023e5494b90c316c183be829.png",
    "singapore-queenstown":     "93406b464a165eaba6d9de76ca09f5da.png",
}

_basemap_cache: dict[str, bytes] = {}

def _process_basemap(location: str) -> bytes:
    filename = _BASEMAP_FILENAMES[location]
    data = read_file(f"maps/{filename}")
    Image.MAX_IMAGE_PIXELS = None  # trusted local files from NuScenes dataset
    img = Image.open(io.BytesIO(data))
    img.thumbnail((4096, 4096), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

@router.get("/maps/{location}/basemap")
async def get_map_basemap(location: str):
    if not re.match(r'^[a-zA-Z0-9_-]+$', location):
        raise HTTPException(status_code=400, detail="Invalid location name")
    if location not in _BASEMAP_FILENAMES:
        raise HTTPException(status_code=404, detail="Basemap not found")

    if location not in _basemap_cache:
        try:
            _basemap_cache[location] = _process_basemap(location)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Basemap not found")

    return StreamingResponse(
        io.BytesIO(_basemap_cache[location]),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
