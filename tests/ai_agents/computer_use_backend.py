"""Playwright backend for Claude Computer Use — translates tool actions into browser calls."""
import base64

from playwright.sync_api import Page, Error as PlaywrightError

# Display dimensions — must match the tool definition sent to Claude
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 800


class PlaywrightComputerBackend:
    """Translates Claude Computer Use actions into Playwright calls.

    Takes screenshots via page.screenshot() and returns base64-encoded PNGs.
    Executes mouse/keyboard actions via Playwright's input API.
    """

    def __init__(self, page: Page):
        self.page = page
        self.page.set_viewport_size({"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT})

    def screenshot(self) -> str:
        """Take screenshot, return base64-encoded PNG string."""
        png_bytes = self.page.screenshot()
        return base64.standard_b64encode(png_bytes).decode("utf-8")

    def left_click(self, x: int, y: int) -> None:
        """Left-click at (x, y)."""
        self.page.mouse.click(x, y)

    def right_click(self, x: int, y: int) -> None:
        """Right-click at (x, y)."""
        self.page.mouse.click(x, y, button="right")

    def double_click(self, x: int, y: int) -> None:
        """Double-click at (x, y)."""
        self.page.mouse.dblclick(x, y)

    def triple_click(self, x: int, y: int) -> None:
        """Triple-click at (x, y) — selects a full line of text."""
        self.page.mouse.click(x, y, click_count=3)

    def type_text(self, text: str) -> None:
        """Type text via keyboard."""
        self.page.keyboard.type(text)

    def key(self, key_combo: str) -> None:
        """Press a key or key combination (e.g. 'Return', 'ctrl+a')."""
        self.page.keyboard.press(key_combo)

    def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        """Scroll at position (x, y) in the given direction."""
        self.page.mouse.move(x, y)
        delta = amount * 100  # pixels per scroll unit
        delta_x = 0
        delta_y = 0
        if direction == "down":
            delta_y = delta
        elif direction == "up":
            delta_y = -delta
        elif direction == "right":
            delta_x = delta
        elif direction == "left":
            delta_x = -delta
        self.page.mouse.wheel(delta_x, delta_y)

    def mouse_move(self, x: int, y: int) -> None:
        """Move mouse to (x, y) without clicking."""
        self.page.mouse.move(x, y)

    def execute_action(self, action: str, params: dict) -> str:
        """Dispatch a Computer Use action and return a screenshot.

        For 'screenshot', returns the base64 string directly.
        For all other actions, executes the action then takes a screenshot.
        On PlaywrightError, returns a screenshot of the error state.
        """
        try:
            if action == "screenshot":
                return self.screenshot()
            elif action == "left_click":
                x, y = params["coordinate"]
                self.left_click(x, y)
            elif action == "right_click":
                x, y = params["coordinate"]
                self.right_click(x, y)
            elif action == "double_click":
                x, y = params["coordinate"]
                self.double_click(x, y)
            elif action == "triple_click":
                x, y = params["coordinate"]
                self.triple_click(x, y)
            elif action == "type":
                self.type_text(params["text"])
            elif action == "key":
                self.key(params.get("key") or params.get("text", "Return"))
            elif action == "scroll":
                x, y = params["coordinate"]
                self.scroll(x, y, params["scroll_direction"], params["scroll_amount"])
            elif action == "mouse_move":
                x, y = params["coordinate"]
                self.mouse_move(x, y)
            return self.screenshot()
        except PlaywrightError:
            # Return screenshot of error state so Claude can see what happened
            return self.screenshot()
