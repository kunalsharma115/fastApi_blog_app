import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image , ImageOps

PROFILE_PIC_DIR = Path("media/profile_pics")

def process_file_image(content:bytes) -> str:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)

        img = ImageOps.fit(img , (300 , 300), method=Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")


        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = PROFILE_PIC_DIR/ filename


        PROFILE_PIC_DIR.mkdir(parents=True , exist_ok=True)

        img.save(filepath , "JPEG", quality = 85 , optimize = True)

    return filename


def delete_profile_pic(filename : str | None = None) -> None:
    if filename is None:
        return 

    filepath = PROFILE_PIC_DIR / filename

    if filepath.exists():
        filepath.unlink()
