import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies import get_db
from app.repositories.sensor import SensorRepository
from app.lib.storage import get_presigned_url, read_file

_IMAGE_FORMATS = {"jpg", "jpeg", "png"}

router = APIRouter(tags=["sensors"])

@router.get("/sensor-data/{token}/image")
async def get_sensor_data_image(token: str, db: AsyncSession = Depends(get_db)):
    sd = await SensorRepository(db).get_sample_data_by_token(token)
    if not sd:
        raise HTTPException(status_code=404, detail="SampleData not found")
    if sd.fileformat.lower() not in _IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail=f"Not an image: {sd.fileformat}")

    # 署名付きURL
    if settings.DEPLOY_ENV == "aws":
        expires_in = 1800  # 署名付きURLの有効期限（秒）。ユースケースに応じて調整。
        url = get_presigned_url(sd.filename, expires_in=expires_in)
        json_ttl = 300  # クライアントがURLを再利用できるように、TTLを署名付きURLの有効期限より短く設定
        return JSONResponse(
            {"url": url, "expires_in": expires_in},
            headers={"Cache-Control": f"private, max-age={json_ttl}"}  # ブラウザにだけキャッシュ（共有キャッシュは避ける）
        )

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
