import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies import get_db
from app.repositories.sensor import SensorRepository
from app.lib.storage import get_cloudfront_url, read_file

_IMAGE_FORMATS = {"jpg", "jpeg", "png"}

router = APIRouter(tags=["sensors"])

@router.get("/sensor-data/{token}/image")
async def get_sensor_data_image(token: str, db: AsyncSession = Depends(get_db)):
    sd = await SensorRepository(db).get_sample_data_by_token(token)
    if not sd:
        raise HTTPException(status_code=404, detail="SampleData not found")
    if sd.fileformat.lower() not in _IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail=f"Not an image: {sd.fileformat}")

    if settings.DEPLOY_ENV == "aws":
        return JSONResponse({"url": get_cloudfront_url(sd.filename)})

    try:
        data = read_file(sd.filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image file not found")

    media_type = "image/png" if sd.fileformat.lower() == "png" else "image/jpeg"
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Length": str(len(data)), "Cache-Control": "public, max-age=86400"},
    )
