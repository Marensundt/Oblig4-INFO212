"""Image services (OB4 A2; US-05). The Claude API is never called: a fake client stands in."""
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app.models.entities import FoodItem
from app.models.image_service import (
    CLAUDE_MODEL,
    ClaudeSvgImageService,
    PlaceholderImageService,
    build_image_service,
)
from app.models.images import ImageError, check_svg

ITEM = FoodItem("Fish soup", "Bergen cod", 189, 10, id=1)
GOOD_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><circle cx="200" cy="150" r="80"/></svg>'


class FakeClient:
    """Records the request and returns a canned response (or raises)."""

    def __init__(self, text=GOOD_SVG, stop_reason="end_turn", error=None):
        self.calls = []
        self.text, self.stop_reason, self.error = text, stop_reason, error
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        content = [SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=self.text)]
        return SimpleNamespace(content=content, stop_reason=self.stop_reason)


def api_error(cls, status):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("failed", response=httpx2.Response(status, request=request), body=None)


def test_placeholder_makes_safe_svg_with_name_and_instruction():
    svg = PlaceholderImageService().create_svg(ITEM, "Steaming <bowl> & dill")
    check_svg(svg)
    assert "Fish soup" in svg
    assert "Steaming &lt;bowl&gt; &amp; dill" in svg


def test_claude_request():
    client = FakeClient()
    svg = ClaudeSvgImageService(client).create_svg(ITEM, "White bowl, dill on top")
    assert svg == GOOD_SVG
    [call] = client.calls
    assert call["model"] == CLAUDE_MODEL == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["output_config"] == {"effort": "medium"}
    assert "thinking" not in call and "temperature" not in call
    prompt = call["messages"][0]["content"]
    assert "Fish soup" in prompt and "White bowl, dill on top" in prompt
    assert "SVG" in call["system"]


def test_claude_modify_sends_current_svg():
    client = FakeClient()
    ClaudeSvgImageService(client).create_svg(ITEM, "Make the bowl blue", current_svg=GOOD_SVG)
    prompt = client.calls[0]["messages"][0]["content"]
    assert prompt.startswith("Modify this SVG")
    assert GOOD_SVG in prompt


def test_claude_svg_extracted_from_surrounding_text():
    client = FakeClient(text=f"Here it is:\n```svg\n{GOOD_SVG}\n```")
    assert ClaudeSvgImageService(client).create_svg(ITEM, "x") == GOOD_SVG


@pytest.mark.parametrize("client,message", [
    (FakeClient(stop_reason="refusal", text=""), "declined"),
    (FakeClient(stop_reason="max_tokens", text="<svg"), "too large"),
    (FakeClient(text="Sorry, I cannot draw."), "did not return a picture"),
    (FakeClient(text='<svg xmlns="http://www.w3.org/2000/svg"><script>x</script></svg>'), "may not contain"),
    (FakeClient(error=api_error(anthropic.AuthenticationError, 401)), "API key"),
    (FakeClient(error=api_error(anthropic.RateLimitError, 429)), "busy"),
    (FakeClient(error=api_error(anthropic.InternalServerError, 500)), "HTTP 500"),
    (FakeClient(error=anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com"))), "Could not reach"),
])
def test_claude_failures_become_image_errors(client, message):
    with pytest.raises(ImageError, match=message):
        ClaudeSvgImageService(client).create_svg(ITEM, "x")


def test_factory_uses_placeholder_without_key():
    assert isinstance(build_image_service({"ANTHROPIC_API_KEY": ""}), PlaceholderImageService)


def test_factory_uses_claude_with_key():
    service = build_image_service({"ANTHROPIC_API_KEY": "test-key-not-real"})
    assert isinstance(service, ClaudeSvgImageService)
