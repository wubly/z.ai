from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from zai.selectors import CHAT_URL, SELECTORS


class BrowserSession:
    def __init__(
        self,
        *,
        headless: bool = True,
        profile_dir: str | Path | None = None,
    ) -> None:
        self.headless = headless
        self.profile_dir = Path(profile_dir) if profile_dir else None
        self._driver: webdriver.Chrome | None = None

    @property
    def driver(self) -> webdriver.Chrome:
        if self._driver is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._driver

    def start(self) -> None:
        if self._driver is not None:
            return

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,900")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.profile_dir is not None:
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={self.profile_dir.resolve()}")

        service = Service(ChromeDriverManager().install())
        self._driver = webdriver.Chrome(service=service, options=options)
        self._driver.get(CHAT_URL)
        self.wait_for_ready()

    def close(self) -> None:
        if self._driver is not None:
            self._driver.quit()
            self._driver = None

    def open_new_chat(self) -> None:
        self.driver.get(CHAT_URL)
        self.wait_for_ready()

    def wait_for_ready(self) -> None:
        self.wait_visible("chat_input", timeout=30)
        self.dismiss_popups()

    def dismiss_popups(self, timeout: float = 2.0) -> None:
        deadline = time.monotonic() + timeout
        dismissed_any = False
        while time.monotonic() < deadline:
            closers = self.find_elements("dialog_close")
            if not closers:
                if dismissed_any:
                    return
                time.sleep(0.1)
                continue
            for closer in closers:
                try:
                    closer.click()
                except Exception:
                    pass
            dismissed_any = True
            time.sleep(0.2)

    def wait_visible(self, key: str, timeout: float = 120.0) -> WebElement:
        by, selector = SELECTORS[key]
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )

    def find_elements(self, key: str) -> list[WebElement]:
        by, selector = SELECTORS[key]
        return self.driver.find_elements(by, selector)

    def type_message(self, message: str, timeout: float = 120.0) -> None:
        try:
            self._fill_chat_input(message, timeout)
        except ElementNotInteractableException:
            self.dismiss_popups()
            self._fill_chat_input(message, timeout)

    def _fill_chat_input(self, message: str, timeout: float) -> None:
        chat_input = self.wait_visible("chat_input", timeout=timeout)
        chat_input.click()
        chat_input.clear()
        if message:
            chat_input.send_keys(message)

    def press_enter(self, timeout: float = 120.0) -> None:
        self.wait_visible("chat_input", timeout=timeout).send_keys(Keys.ENTER)

    def click_send(self, timeout: float = 10.0) -> None:
        send_btn = self.wait_visible("send_button", timeout=timeout)
        WebDriverWait(self.driver, timeout).until(
            lambda d: send_btn.is_enabled() and send_btn.get_attribute("disabled") is None
        )
        send_btn.click()

    def set_deep_think(self, enabled: bool, timeout: float = 10.0) -> None:
        button = self.wait_visible("deep_think_button", timeout=timeout)
        current = button.get_attribute("data-autothink") == "true"
        if current != enabled:
            button.click()

    def upload_files(self, files: Sequence[str | Path]) -> None:
        paths = [str(Path(f).resolve()) for f in files]
        for path in paths:
            if not Path(path).is_file():
                raise FileNotFoundError(path)

        file_input = self.driver.find_element(*SELECTORS["file_input"])
        file_input.send_keys("\n".join(paths))
        time.sleep(0.5)

    def latest_assistant_message(self, prior_count: int) -> WebElement | None:
        messages = self.find_elements("assistant_messages")
        if len(messages) <= prior_count:
            return None
        return messages[-1]

    def extract_thinking(self, assistant_el: WebElement) -> str:
        by, selector = SELECTORS["thinking_blocks"]
        blocks = assistant_el.find_elements(by, selector)
        if not blocks:
            return ""
        return blocks[-1].text.strip()

    def extract_visible_text(self, assistant_el: WebElement) -> str:
        by, selector = SELECTORS["response_paragraphs"]
        paragraphs = assistant_el.find_elements(by, selector)
        parts = [p.text.strip() for p in paragraphs if p.text.strip()]
        return "\n\n".join(parts)

    def message_id_for(self, assistant_el: WebElement) -> str | None:
        by, selector = SELECTORS["message_container"]
        container = assistant_el.find_elements(by, selector)
        if not container:
            return None
        return container[0].get_attribute("id")
