from datetime import timedelta
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException


load_dotenv()
router = APIRouter()

try:
    import alibabacloud_oss_v2 as oss
except ImportError:
    oss = None

if oss is not None:
    credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    cfg.region = os.getenv("OSS_REGION", "cn-beijing")
    client = oss.Client(cfg)
else:
    client = None

OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
OSS_BUCKET = os.getenv("OSS_BUCKET")


@router.get("/oss/presign")
def get_oss_presign_url(filename: str):
    if oss is None or client is None:
        raise HTTPException(status_code=503, detail="OSS SDK 未安装，当前只能使用文字聊天")
    if not OSS_BUCKET:
        raise HTTPException(status_code=503, detail="缺少 OSS_BUCKET 环境变量")

    content_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = content_type_map.get(ext, "application/octet-stream")

    pre_result = client.presign(
        oss.PutObjectRequest(
            bucket=OSS_BUCKET,
            key=filename,
            content_type=content_type,
        ),
        expires=timedelta(seconds=3600),
    )

    return {
        "uploadUrl": pre_result.url.strip('"'),
        "contentType": content_type,
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}",
    }
