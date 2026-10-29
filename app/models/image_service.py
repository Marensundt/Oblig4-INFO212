"""Create or modify a food item picture from an admin's instruction (OB4 A2; US-05; OPEN-4).

Claude cannot output bitmaps, so the AI service writes an SVG (ASSUMPTION, docs/plans/09).
The offline placeholder is the default; the Claude service is used only when ANTHROPIC_API_KEY is set.
"""
import hashlib
import re
from abc import ABC, abstractmethod
from html import escape
from textwrap import wrap

from app.models.images import ImageError, check_svg

CLAUDE_MODEL = "claude-opus-5-5"

_SVG_BLOCK = re.compile(r"<svg\b.*?</svg>", re.S | re.I)


class ImageService(ABC):
    name = ""

    @abstractmethod
    def create_svg(self, item, instruction, current_svg=None):
        """Return SVG text for the item. With current_svg, modify that picture. Raises ImageError."""


class PlaceholderImageService(ImageService):
    """Offline default: a simple illustrated card with the item name and the instruction."""

    name = "offline placeholder"

    def create_svg(self, item, instruction, current_svg=None):
        hue = int(hashlib.sha256(item.name.encode("utf-8")).hexdigest()[:4], 16) % 360
        lines = wrap(instruction, 46)[:3]
        caption = "".join(
            f'<text x="200" y="{258 + i * 16}" font-size="13" text-anchor="middle" fill="#444">{escape(line)}</text>'
            for i, line in enumerate(lines)
        )
        title = escape(item.name if len(item.name) <= 34 else item.name[:33] + "…")
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300" role="img">'
            f"<title>{escape(item.name)}</title>"
            f'<rect width="400" height="300" fill="hsl({hue}, 45%, 88%)"/>'
            '<ellipse cx="200" cy="120" rx="120" ry="70" fill="#fff" stroke="#ccc" stroke-width="3"/>'
            f'<ellipse cx="200" cy="115" rx="70" ry="38" fill="hsl({hue}, 50%, 55%)"/>'
            f'<text x="200" y="225" font-size="20" font-weight="bold" text-anchor="middle" fill="#222">{title}</text>'
            f"{caption}</svg>"
        )


class ClaudeSvgImageService(ImageService):
    """Asks Claude to write or modify an SVG. `client` is an anthropic.Anthropic (a fake in tests)."""

    name = "Claude"

    SYSTEM = (
        "You draw appetising, simple illustrations of catering dishes for the menu of Ekte Mat, "
        "a Bergen caterer. Reply with one complete SVG document and nothing else: "
        'root <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">, flat shapes and gradients, '
        "no text unless asked, no <script>, no event handlers, no <foreignObject>, no external links, "
        "images or fonts. Keep it under 30 KB."
    )

    def __init__(self, client):
        self.client = client

    def create_svg(self, item, instruction, current_svg=None):
        import anthropic

        prompt = f"Dish: {item.name}\nDescription: {item.description or '-'}\nInstruction: {instruction}"
        if current_svg:
            prompt = f"Modify this SVG picture according to the instruction.\n\n{current_svg}\n\n{prompt}"
        try:
            response = self.client.beta.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=16000,
                output_config={"effort": "medium"},
                # On a safety decline the API retries on a suitable fallback model in the same call
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=self.SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.AuthenticationError:
            raise ImageError("The AI image service rejected the API key. Check ANTHROPIC_API_KEY in .env.") from None
        except anthropic.RateLimitError:
            raise ImageError("The AI image service is busy. Try again in a minute.") from None
        except anthropic.APIStatusError as error:
            raise ImageError(f"The AI image service failed (HTTP {error.status_code}). Try again later.") from None
        except anthropic.APIConnectionError:
            raise ImageError("Could not reach the AI image service. Check the internet connection.") from None

        if response.stop_reason == "refusal":
            raise ImageError("The AI image service declined this instruction. Try a different wording.")
        if response.stop_reason == "max_tokens":
            raise ImageError("The picture was too large to finish. Ask for a simpler picture.")
        text = "".join(block.text for block in response.content if block.type == "text")
        match = _SVG_BLOCK.search(text)
        if not match:
            raise ImageError("The AI image service did not return a picture. Try again.")
        svg = match.group(0)
        check_svg(svg)  # never trust generated markup more than an upload
        return svg


def build_image_service(config):
    """Claude if an API key is configured and the SDK is installed, otherwise the offline placeholder."""
    if config.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
        except ImportError:
            return PlaceholderImageService()
        return ClaudeSvgImageService(anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"]))
    return PlaceholderImageService()
