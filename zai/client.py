from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Sequence

from selenium.common.exceptions import TimeoutException

from zai.browser import BrowserSession
from zai.models import ZaiResponse


class ZaiClient:
    def __init__(
        self,
        *,
        headless: bool = True,
        profile_dir: str | Path | None = None,
        timeout: float = 120.0,
        poll_interval: float = 0.5,
        stable_seconds: float = 2.0,
    ) -> None:
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.stable_seconds = stable_seconds
        self._browser = BrowserSession(headless=headless, profile_dir=profile_dir)

    def __enter__(self) -> ZaiClient:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def start(self) -> None:
        self._browser.start()

    def close(self) -> None:
        self._browser.close()

    def new_chat(self) -> None:
        self._browser.open_new_chat()

    def send(
        self,
        message: str,
        *,
        files: Sequence[str | Path] | None = None,
        deep_think: bool | None = None,
        include_thinking: bool = True,
        include_raw_html: bool = False,
        on_thinking: Callable[[str], None] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> ZaiResponse:
        message = message.strip()
        if not message and not files:
            raise ValueError("message or files required")

        if deep_think is not None:
            self._browser.set_deep_think(deep_think)

        if files:
            self._browser.upload_files(files)

        prior_count = len(self._browser.find_elements("assistant_messages"))
        self._browser.type_message(message, timeout=self.timeout)
        self._browser.click_send()

        self._wait_for_new_assistant_message(prior_count)
        thinking_seconds = self._wait_for_generation(
            prior_count,
            on_thinking=on_thinking,
            on_text=on_text,
        )

        return self._parse_latest_response(
            prior_count,
            thinking_seconds=thinking_seconds,
            include_thinking=include_thinking,
            include_raw_html=include_raw_html,
        )

    def send_and_stream_text(
        self,
        message: str,
        *,
        on_chunk: Callable[[str], None] | None = None,
        on_thinking: Callable[[str], None] | None = None,
        files: Sequence[str | Path] | None = None,
        deep_think: bool | None = None,
        include_thinking: bool = True,
        include_raw_html: bool = False,
    ) -> ZaiResponse:
        return self.send(
            message,
            files=files,
            deep_think=deep_think,
            include_thinking=include_thinking,
            include_raw_html=include_raw_html,
            on_thinking=on_thinking,
            on_text=on_chunk,
        )

    def submit_with_enter(self, message: str) -> ZaiResponse:
        message = message.strip()
        prior_count = len(self._browser.find_elements("assistant_messages"))
        self._browser.type_message(message, timeout=self.timeout)
        self._browser.press_enter(timeout=self.timeout)

        self._wait_for_new_assistant_message(prior_count)
        thinking_seconds = self._wait_for_generation(prior_count)
        return self._parse_latest_response(prior_count, thinking_seconds=thinking_seconds)

    def _wait_for_new_assistant_message(self, prior_count: int) -> None:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self._browser.latest_assistant_message(prior_count) is not None:
                return
            time.sleep(self.poll_interval)
        raise TimeoutException(f"No new assistant message within {self.timeout}s")

    def _wait_for_generation(
        self,
        prior_count: int,
        *,
        on_thinking: Callable[[str], None] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> float | None:
        deadline = time.monotonic() + self.timeout
        last_text = ""
        last_thinking = ""
        stable_since: float | None = None
        thinking_start: float | None = None
        thinking_seconds: float | None = None

        while time.monotonic() < deadline:
            assistant_el = self._browser.latest_assistant_message(prior_count)
            if assistant_el is None:
                time.sleep(self.poll_interval)
                continue

            try:
                current_text = self._browser.extract_visible_text(assistant_el)
                current_thinking = self._browser.extract_thinking(assistant_el)
            except Exception:
                time.sleep(self.poll_interval)
                continue

            if current_thinking and thinking_start is None:
                thinking_start = time.monotonic()

            if current_thinking != last_thinking:
                last_thinking = current_thinking
                if on_thinking is not None and current_thinking:
                    on_thinking(current_thinking)

            if current_text and thinking_start is not None and thinking_seconds is None:
                thinking_seconds = time.monotonic() - thinking_start

            if current_text != last_text:
                last_text = current_text
                stable_since = None
                if on_text is not None and current_text:
                    on_text(current_text)
            elif current_text:
                if stable_since is None:
                    stable_since = time.monotonic()
                elif time.monotonic() - stable_since >= self.stable_seconds:
                    return thinking_seconds

            time.sleep(self.poll_interval)

        if last_text:
            return thinking_seconds
        raise TimeoutException(f"Response did not stabilize within {self.timeout}s")

    def _parse_latest_response(
        self,
        prior_count: int,
        *,
        thinking_seconds: float | None = None,
        include_thinking: bool = True,
        include_raw_html: bool = False,
    ) -> ZaiResponse:
        assistant_el = self._browser.latest_assistant_message(prior_count)
        if assistant_el is None:
            raise TimeoutException("Assistant message disappeared before parsing")

        thinking = None
        if include_thinking:
            thinking = self._browser.extract_thinking(assistant_el) or None

        text = self._browser.extract_visible_text(assistant_el)
        raw_html = assistant_el.get_attribute("innerHTML") if include_raw_html else None
        message_id = self._browser.message_id_for(assistant_el)

        return ZaiResponse(
            text=text,
            thinking=thinking,
            thinking_seconds=thinking_seconds if thinking else None,
            message_id=message_id,
            raw_html=raw_html,
        )
