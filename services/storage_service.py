"""Armazenamento privado de QR Codes em um endpoint compatível com S3, como o MinIO."""

import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def _settings():
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "").strip(),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "").strip(),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "").strip(),
        "bucket": os.getenv("MINIO_BUCKET", "blockchain").strip(),
        "region": os.getenv("MINIO_REGION", "us-east-1").strip(),
        "prefix": os.getenv("MINIO_QR_PREFIX", "qrcodes").strip("/"),
    }


def _is_configured(settings):
    return all(settings[key] for key in ("endpoint", "access_key", "secret_key", "bucket"))


def _client(settings):
    return boto3.client(
        "s3",
        endpoint_url=settings["endpoint"],
        aws_access_key_id=settings["access_key"],
        aws_secret_access_key=settings["secret_key"],
        region_name=settings["region"],
        config=Config(signature_version="s3v4"),
    )


def _object_key(product_id, settings):
    return f"{settings['prefix']}/{product_id}.png" if settings["prefix"] else f"{product_id}.png"


def upload_qr_code(product_id, image_bytes):
    """Envia o PNG após o registro on-chain; retorna None quando o MinIO não foi configurado."""
    settings = _settings()
    if not _is_configured(settings):
        return None

    object_key = _object_key(product_id, settings)
    _client(settings).put_object(
        Bucket=settings["bucket"],
        Key=object_key,
        Body=image_bytes,
        ContentType="image/png",
        CacheControl="private, max-age=3600",
    )
    return object_key


def get_qr_code_url(product_id, expires_in=900):
    """Gera uma URL temporária para exibir um QR Code sem tornar o bucket público."""
    settings = _settings()
    if not _is_configured(settings):
        return None

    object_key = _object_key(product_id, settings)
    try:
        return _client(settings).generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings["bucket"],
                "Key": object_key,
                "ResponseContentType": "image/png",
            },
            ExpiresIn=expires_in,
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "erro desconhecido")
        if error_code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            return None
        raise RuntimeError(f"O armazenamento de arquivos respondeu com {error_code}.") from error
