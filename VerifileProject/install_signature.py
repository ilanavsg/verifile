import io

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from PIL import Image, PngImagePlugin, ImageDraw,  ImageFont


def install_watermark(img_rgba):
    watermarked = img_rgba.copy()
    draw = ImageDraw.Draw(watermarked)

    circle_radius = max(10, img_rgba.width // 50)
    margin = circle_radius + 5
    x = img_rgba.width - circle_radius - margin
    y = img_rgba.height - circle_radius - margin

    draw.ellipse(
        (x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius),
        fill=(255, 182, 193, 120)
    )

    try:
        font = ImageFont.truetype("ariali.ttf", circle_radius)
    except IOError:
        font = ImageFont.load_default()

    text = "Verifile"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw.text(
        (x - text_w/2, y - text_h/2),
        text,
        font=font,
        fill=(255, 255, 255, 200)
    )
    return watermarked


class Signature:

    def __init__(self, img_path, private_key_path=None, public_key_path=None, watermarked_path=None):
        self.img_path = img_path
        self.private = private_key_path
        self.public = public_key_path
        self.watermarked = watermarked_path

    def _hash_image(self, img_path=None):
        """Compute SHA-256 hash of the image data."""
        if not img_path:
            img_path = self.img_path
        with open(img_path, "rb") as f:
            data = f.read()
        return SHA256.new(data)

    def install_sign_to_img(self):
        img = Image.open(self.img_path).convert("RGBA")
        watermarked = install_watermark(img)

        # 🔐 HASH PIXEL DATA (DETERMINISTIC)
        pixel_bytes = watermarked.tobytes()
        meta_data = f"{watermarked.size}{watermarked.mode}".encode()

        h = SHA256.new(pixel_bytes + meta_data)

        private_key = RSA.import_key(open(self.private, "rb").read())
        signature = pss.new(private_key).sign(h)

        meta = PngImagePlugin.PngInfo()
        meta.add_text("Signature", signature.hex())
        meta.add_text("HashAlg", "SHA256")
        meta.add_text("Mode", watermarked.mode)
        meta.add_text("Size", f"{watermarked.size[0]}x{watermarked.size[1]}")

        watermarked.save(self.watermarked, "PNG", pnginfo=meta)

    def verify_signature(self, image_path=None):
        if not image_path:
            image_path = self.img_path

        img = Image.open(image_path).convert("RGBA")

        signature_hex = img.info.get("Signature")
        if not signature_hex:
            return False, "No signature found"

        signature = bytes.fromhex(signature_hex)

        # 🔐 SAME HASH METHOD
        pixel_bytes = img.tobytes()
        meta_data = f"{img.size}{img.mode}".encode()
        h = SHA256.new(pixel_bytes + meta_data)

        public_key = RSA.import_key(open(self.public, "rb").read())
        verifier = pss.new(public_key)

        try:
            verifier.verify(h, signature)
            return True, "Signature valid"
        except (ValueError, TypeError):
            return False, "Signature verification failed"
