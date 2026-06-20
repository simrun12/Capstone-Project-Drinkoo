"""File upload routes for DRINKOO."""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from .auth import get_current_user
from ..config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE_BYTES, UPLOAD_DIRECTORY
from ..database.db import get_db
from ..utils.auth import AuthenticatedUser

router = APIRouter(prefix="/upload", tags=["uploads"])


@router.post("/sku-images/")
async def upload_sku_image(
    sku_id: int,
    upload_file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    """Upload a SKU image for DRINKOO."""

    db = get_db()
    sku = db.fetch_one("SELECT sku_code FROM skus WHERE sku_id = ?", (sku_id,))

    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    if upload_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, and WEBP images are allowed",
        )

    file_contents = await upload_file.read()
    if len(file_contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image file is too large",
        )

    upload_folder = os.path.join(UPLOAD_DIRECTORY, "sku_images")
    os.makedirs(upload_folder, exist_ok=True)

    safe_filename = upload_file.filename.replace(" ", "_") if upload_file.filename else "drinkoo_sku_image.png"
    stored_filename = f"{sku_id}_{int(time.time())}_{safe_filename}"
    file_path = os.path.join(upload_folder, stored_filename)

    with open(file_path, "wb") as output_file:
        output_file.write(file_contents)

    db.execute(
        """
        INSERT INTO sku_images (
            sku_id,
            image_path,
            image_filename,
            file_size,
            mime_type
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            sku_id,
            file_path,
            stored_filename,
            len(file_contents),
            upload_file.content_type,
        ),
    )
    db.commit()

    return {
        "message": "SKU image uploaded successfully",
        "sku_id": sku_id,
        "image_path": file_path,
        "image_filename": stored_filename,
    }
