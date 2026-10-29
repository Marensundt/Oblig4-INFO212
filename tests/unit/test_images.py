"""Picture validation and storage (OB4 A2; US-04)."""
import pytest

from app.models.images import ImageError, ImageStorage, check_instruction, check_svg, check_upload

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle r="4" fill="url(#g)"/></svg>'


@pytest.mark.parametrize("name,data,ext", [
    ("soup.png", PNG, "png"), ("SOUP.JPG", JPG, "jpg"), ("soup.jpeg", JPG, "jpg"),
    ("soup.webp", WEBP, "webp"), ("soup.svg", SVG, "svg"),
])
def test_accepted_uploads(name, data, ext):
    assert check_upload(name, data) == ext


@pytest.mark.parametrize("name,data,message", [
    ("soup.gif", b"GIF89a", "JPG, PNG, WebP or SVG"),
    ("soup", PNG, "JPG, PNG, WebP or SVG"),
    ("soup.png", b"", "empty"),
    ("soup.png", JPG, "does not look like a PNG"),
    ("notes.png", b"hello world", "does not look like a PNG"),
])
def test_refused_uploads(name, data, message):
    with pytest.raises(ImageError, match=message):
        check_upload(name, data)


@pytest.mark.parametrize("svg", [
    '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><rect onclick="alert(1)"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><div/></foreignObject></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
    '<image xlink:href="https://evil.example/x.png"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><rect/></a></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><rect style="fill:url(https://evil.example/x)"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(x.css);</style></svg>',
    '<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa">]><svg xmlns="http://www.w3.org/2000/svg">&a;</svg>',
    '<svg xmlns="http://www.w3.org/2000/svg"><rect></svg>',
    '<html><svg/></html>',
])
def test_unsafe_or_broken_svg_refused(svg):
    with pytest.raises(ImageError):
        check_svg(svg)


def test_safe_svg_with_internal_references():
    check_svg('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
              '<defs><linearGradient id="g"/><circle id="c" r="2"/></defs>'
              '<use xlink:href="#c"/><rect fill="url(#g)"/></svg>')


def test_instruction_rules():
    assert check_instruction("  Fish soup with dill  ") == "Fish soup with dill"
    with pytest.raises(ImageError, match="Write an instruction"):
        check_instruction("   ")
    with pytest.raises(ImageError, match="at most 500"):
        check_instruction("x" * 501)


def test_storage_pending_save_and_delete(tmp_path):
    storage = ImageStorage(str(tmp_path))
    name = storage.add_pending(7, "png", PNG)
    assert name.startswith("item-7-") and name.endswith(".png")
    assert storage.read(name) is None  # not visible until saved
    assert storage.save_pending(name) == name
    assert storage.read(name) == PNG
    storage.delete(name)
    assert storage.read(name) is None


def test_storage_discard(tmp_path):
    storage = ImageStorage(str(tmp_path))
    name = storage.add_pending(7, "svg", SVG)
    storage.discard_pending(name)
    with pytest.raises(ImageError):
        storage.pending_path(name)
    storage.discard_pending(name)  # twice is harmless


def test_storage_refuses_path_tricks_and_keeps_other_files(tmp_path):
    storage = ImageStorage(str(tmp_path))
    for bad in ("../secret.png", ".hidden", "a/b.png"):
        with pytest.raises(ImageError):
            storage.pending_path(bad)
    (tmp_path / "demo.png").write_bytes(PNG)
    storage.delete("demo.png")  # not a generated name: seed/demo pictures are kept
    assert (tmp_path / "demo.png").exists()
