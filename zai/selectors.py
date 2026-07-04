from selenium.webdriver.common.by import By

CHAT_URL = "https://chat.z.ai/"

SELECTORS = {
    "chat_input": (By.CSS_SELECTOR, "#chat-input"),
    "send_button": (By.CSS_SELECTOR, "#send-message-button"),
    "file_input": (By.CSS_SELECTOR, 'input[type="file"]'),
    "assistant_messages": (By.CSS_SELECTOR, ".chat-assistant"),
    "thinking_blocks": (By.CSS_SELECTOR, ".thinking-block blockquote"),
    "response_paragraphs": (By.CSS_SELECTOR, "#response-content-container .markdown-prose > p"),
    "deep_think_button": (By.CSS_SELECTOR, "button[data-autothink]"),
    "dialog_close": (By.CSS_SELECTOR, "[data-dialog-close]"),
    "message_container": (By.XPATH, "./ancestor::div[starts-with(@id, 'message-')]"),
}
