# Copyright (c) 2024 Seweryn Rusecki

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from libqtile.command.base import expose_command
from libqtile.widget import base

if TYPE_CHECKING:
    from typing import Any, Callable


def get_touchpad_device_name() -> str:
    properties = subprocess.check_output(["xinput", "list", "--name-only"], text=True)

    for line in properties.splitlines():
        if "touchpad" in line.lower():
            return line

    raise RuntimeError("Could not determine touchpad name automatically!")


def get_touchpad_enabled(device_id: str) -> bool:
    properties = subprocess.check_output(["xinput", "list-props", device_id], text=True)

    for line in properties.splitlines():
        if "device enabled" in line.lower():
            return line[-1] == "1"

    raise RuntimeError("Could not determine touchpad state automatically!")


def set_touchpad_enabled(device_id: str, state: bool) -> None:
    subprocess.run(["xinput", "enable" if state else "disable", device_id])


class Touchpad(base.ThreadPoolText):
    """
    A simple widget to display touchpad state.

    You can also bind keyboard shortcuts to the Touchpad widget with:

    .. code-block:: python

        Key(
            [],
            "XF86TouchpadToggle",
            lazy.widget["touchpad"].toggle()
        )
    """

    device_id: None | str
    get_state_func: None | Callable[[str], bool]
    set_state_func: None | Callable[[str, bool], None]

    supported_backends = {"x11"}

    defaults: list[tuple[str, Any, str]] = [
        (
            "device_id",
            None,
            "Touchpad name or id, provided as ``str``. "
            "If set to ``None`` the widget will try to find it automatically using ``xinput``.",
        ),
        (
            "get_state_func",
            None,
            "Function which can read the touchpad state. "
            "It should return the state as ``bool``. "
            "If set to ``None`` a default function based on ``xinput`` will be used.",
        ),
        (
            "set_state_func",
            None,
            "Function which can enable/disable touchpad. "
            "It should take one ``bool`` parameter and change touchpad state accordingly. "
            "If set to ``None`` a default function based on ``xinput`` will be used.",
        ),
        ("format", "{state}", "Displayed text format"),
        ("enabled_char", "[👆]", "State shown when touchpad is enabled"),
        ("disabled_char", "[🚫]", "State shown when touchpad is disabled"),
        (
            "update_interval",
            10,
            "Seconds between status updates. "
            "Additionally, status is updated immediately after calling ``toggle`` command from this class.",
        ),
    ]

    def __init__(self, **config) -> None:
        base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(Touchpad.defaults)

        self.add_callbacks(
            {
                "Button1": self.toggle,
            }
        )

    def _configure(self, qtile, bar) -> None:
        base.ThreadPoolText._configure(self, qtile, bar)

        if self.device_id is None:
            self.device_id = get_touchpad_device_name()
        if self.get_state_func is None:
            self.get_state_func = get_touchpad_enabled
        if self.set_state_func is None:
            self.set_state_func = set_touchpad_enabled

    def poll(self) -> str:
        assert isinstance(self.device_id, str), "device_id has to be a string!"
        assert callable(self.get_state_func), "get_state_func has to be callable!"

        state = self.get_state_func(self.device_id)
        state_text = self.enabled_char if state else self.disabled_char
        return self.format.format(state=state_text)

    @expose_command()
    def toggle(self) -> None:
        """Toggle touchpad on/off."""

        assert isinstance(self.device_id, str), "device_id has to be a string!"
        assert callable(self.get_state_func), "get_state_func has to be callable!"
        assert callable(self.set_state_func), "set_state_func has to be callable!"

        new_state = not self.get_state_func(self.device_id)
        self.set_state_func(self.device_id, new_state)
        self.force_update()

