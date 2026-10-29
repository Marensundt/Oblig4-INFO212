"""Food item pictures (OB4 A2; US-04, US-05): validation and file storage. No Flask imports.

Pictures are files in the upload folder; only the file name is stored on the FoodItem.
A new picture is first kept as "pending" until the admin saves it after the preview.
"""
import os
import re
import secrets
import xml.etree.ElementTree as ET

# Extension -> (media type, check of the first bytes). ASSUMPTION: these four types are enough.
IMAGE_TYPES = {
    "jpg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "jpeg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "png": ("image/png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "webp": ("image/webp", lambda data: data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    "svg": ("image/svg+xml", lambda data: b"<svg" in data[:2048]),
}
MAX_SVG_BYTES = 500 * 1024
MAX_INSTRUCTION_LENGTH = 500

# SVG content that could run code or load other resources (ASSUMPTION: refuse, do not clean).
_FORBIDDEN_TAGS = {"script", "foreignobject", "iframe", "embed", "object", "audio", "video"}
_SAFE_LINK = re.compile(r"^#[\w.-]+$")
# url(...) that does not point to an element inside the same SVG (url(#gradient) is fine), or @import
_EXTERNAL_URL = re.compile(r"url\(\s*['\"]?(?!#)|@import", re.IGNORECASE)


class ImageError(Exception):
    """A picture or instruction is not accepted. The message is shown to the admin."""


def extension_of(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""


def check_upload(filename, data):
    """Return the normalised extension, or raise ImageError (US-04)."""
    ext = extension_of(filename)
    if ext not in IMAGE_TYPES:
        raise ImageError("Choose a JPG, PNG, WebP or SVG file.")
    if not data:
        raise ImageError("The file is empty.")
    _, content_matches = IMAGE_TYPES[ext]
    if not content_matches(data):
        raise ImageError(f"The file does not look like a {ext.upper()} picture.")
    if ext == "svg":
        check_svg(data)
    return "jpg" if ext == "jpeg" else ext


def check_svg(data):
    """Refuse SVGs that could run scripts or load external content (uploaded or AI-generated)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    if len(data) > MAX_SVG_BYTES:
        raise ImageError("The SVG picture is too large.")
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ImageError("SVG pictures with DOCTYPE or entities are not accepted.")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise ImageError("The SVG picture is not valid XML.") from None
    if _local(root.tag) != "svg":
        raise ImageError("The file is not an SVG picture.")
    for element in root.iter():
        if _local(element.tag).lower() in _FORBIDDEN_TAGS:
            raise ImageError(f"SVG pictures may not contain <{_local(element.tag)}>.")
        for name, value in element.attrib.items():
            name = _local(name).lower()
            if name.startswith("on"):
                raise ImageError("SVG pictures may not contain event handlers.")
            if name == "href" and not _SAFE_LINK.match(value.strip()):
                raise ImageError("SVG pictures may not link to other files or pages.")
            if _EXTERNAL_URL.search(value):
                raise ImageError("SVG pictures may not load other files.")
        if _local(element.tag).lower() == "style" and _EXTERNAL_URL.search(element.text or ""):
            raise ImageError("SVG pictures may not load other files.")


def check_instruction(text):
    text = (text or "").strip()
    if not text:
        raise ImageError("Write an instruction first.")
    if len(text) > MAX_INSTRUCTION_LENGTH:
        raise ImageError(f"The instruction can be at most {MAX_INSTRUCTION_LENGTH} characters.")
    return text


def _local(tag):
    """Tag or attribute name without XML namespace."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


class ImageStorage:
    """Pending and saved picture files in the upload folder (the only code that touches them)."""

    PENDING = "pending"

    def __init__(self, folder):
        self.folder = folder

    def _pending_dir(self):
        path = os.path.join(self.folder, self.PENDING)
        os.makedirs(path, exist_ok=True)
        return path

    def add_pending(self, item_id, ext, data):
        """Store a picture waiting for preview; return its generated file name."""
        name = f"item-{item_id}-{secrets.token_hex(8)}.{ext}"
        with open(os.path.join(self._pending_dir(), name), "wb") as f:
            f.write(data)
        return name

    def pending_path(self, name):
        path = os.path.join(self._pending_dir(), _safe_name(name))
        if not os.path.isfile(path):
            raise ImageError("There is no picture waiting for preview. Upload or create one again.")
        return path

    def save_pending(self, name):
        """Move a pending picture into the upload folder; return the file name for FoodItem.image_filename."""
        source = self.pending_path(name)
        os.makedirs(self.folder, exist_ok=True)
        os.replace(source, os.path.join(self.folder, _safe_name(name)))
        return name

    def discard_pending(self, name):
        try:
            os.remove(self.pending_path(name))
        except ImageError:
            pass

    def read(self, filename):
        """Bytes of a saved picture, or None."""
        path = os.path.join(self.folder, _safe_name(filename))
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete(self, filename):
        """Remove a saved picture made by this app (generated names only; seed/demo files are kept)."""
        if filename and re.fullmatch(r"item-\d+-[0-9a-f]{16}\.\w+", filename):
            path = os.path.join(self.folder, filename)
            if os.path.isfile(path):
                os.remove(path)


def _safe_name(name):
    if not re.fullmatch(r"[\w.-]+", name or "") or name.startswith("."):
        raise ImageError("Invalid picture name.")
    return name
