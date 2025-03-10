import subprocess

from libqtile import bar, layout, widget, extension
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.dgroups import simple_key_binder
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal, send_notification
from libqtile.log_utils import logger

import hooks
from colors import dock_color, window_color, transparent
from dmenu import dmenu_run, dmenu_sys, dmenu_exit, dmenu_battery
from settings import *
from groups import SCRATCH_PADS, GROUPS, HIDDEN_GROUPS
from widgets.hideable_gap import HideableGap
from widgets.touchpad import Touchpad
from widgets.powerline import Powerline
from layouts.columns import MyColumns


@lazy.function
def dummy_logger(qtile):
    import random
    logger.warning(f'Dummy warning #{random.randint(1, 100)}')


def log_cleaner():
    return lazy.spawn('bash -c "> /home/seweryn/.local/share/qtile/qtile.log"')


keys = [
    # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html
    # Switch between windows
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key(
        [mod, "shift"],
        "Return",
        lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack",
    ),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
    Key(
        [mod],
        "f",
        lazy.window.toggle_fullscreen(),
        desc="Toggle fullscreen on the focused window",
    ),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating on the focused window"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", dmenu_exit(), desc="Shutdown Qtile"),

    Key([mod], "p", dmenu_run()),
    Key([mod], 'g', dmenu_sys()),

    Key([mod], 'e', lazy.spawn(file_explorer)),
    Key([mod], 'b', lazy.spawn(browser)),

    # next/prev group, used also by libinput-gestures
    Key([mod], 'equal', lazy.screen.next_group()),
    Key([mod], 'minus', lazy.screen.prev_group()),

    Key([mod], 'x', lazy.spawn('alacritty -e watch -n 0.1 tail -n 30 ~/.local/share/qtile/qtile.log')),
    Key([mod, 'control'], 'x', log_cleaner()),
    Key([mod, 'shift'], 'x', dummy_logger),

    Key([mod], 'Print', lazy.spawn('gnome-screenshot')),
    Key([], 'Print', lazy.spawn('gnome-screenshot -i')),

    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set +20")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 20-")),
    
    Key([], "XF86TouchpadToggle", lazy.widget['touchpad'].toggle()),

    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer sset Master 5%-"), desc="Lower Volume by 5%"),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer sset Master 5%+"), desc="Raise Volume by 5%"),
    Key([], "XF86AudioMute", lazy.spawn("amixer sset Master 1+ toggle"), desc="Mute/Unmute Volume"),
    Key([], "XF86AudioPlay", lazy.spawn("playerctl play-pause"), desc="Play/Pause player"),
    Key([], "XF86AudioNext", lazy.spawn("playerctl next"), desc="Skip to next"),
    Key([], "XF86AudioPrev", lazy.spawn("playerctl previous"), desc="Skip to previous"),

    Key([mod], 'grave', lazy.group['scratchpad'].dropdown_toggle('temp')),
]

groups = SCRATCH_PADS + GROUPS + HIDDEN_GROUPS

for n, i in enumerate(groups[len(SCRATCH_PADS):]):
    #continue
    keys.extend(
        [
            # mod1 + letter of group = switch to group
            Key(
                [mod],
                str(n + 1),
                lazy.group[i.name].toscreen(),
                desc="Switch to group {}".format(i.name),
            ),
            # mod1 + shift + letter of group = switch to & move focused window to group
            Key(
                [mod, "shift"],
                str(n + 1),
                lazy.window.togroup(i.name, switch_group=True),
                desc="Switch to & move focused window to group {}".format(i.name),
            ),
            # Or, use below if you prefer not to switch to that group.
            # # mod1 + shift + letter of group = move focused window to group
            # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
            #     desc="move focused window to group {}".format(i.name)),
        ]
    )

layout_defaults = {
    'margin': [margin, margin, 0, 0],
    'border_width': 2,
    'border_on_single': True,
    'border_normal': window_color.inactive_border,
    'border_focus': window_color.active_border,
}

stack_defaults = layout_defaults.copy()
stack_defaults['border_focus'] = stack_defaults['border_normal']

layouts = [
    MyColumns(name='Columns', **layout_defaults),
    layout.Max(name='Stack', **stack_defaults),
    layout.Max(name='Full'),
    # layout.Stack(num_stacks=2),
    # layout.Bsp(),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

widget_defaults = dict(
    font = FONT_BOLD,
    fontsize = 14,
    padding = 5,
    foreground = dock_color.text
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                Powerline(type='open'),
                widget.TextBox(
                    'Menu',
                    background = dock_color.bg1,
                    padding = 10,
                    mouse_callbacks = {
                        'Button1': dmenu_sys()
                    },
                ),
                Powerline(),
                widget.GroupBox(
                    active = dock_color.text,
                    inactive = dock_color.inactive_group_text,
                    background = dock_color.bg2,
                    highlight_method = 'line',
                    highlight_color = [transparent, transparent],
                    this_current_screen_border = dock_color.active_group_highlight,
                    visible_groups = [g.name for g in GROUPS],
                ),
                widget.GroupBox(
                    active = dock_color.text,
                    inactive = dock_color.inactive_group_text,
                    background = dock_color.bg2,
                    highlight_method = 'line',
                    highlight_color = [transparent, transparent],
                    this_current_screen_border = dock_color.active_group_highlight,
                    visible_groups = [g.name for g in HIDDEN_GROUPS],
                    hide_unused = True,
                ),
                Powerline(),
                widget.CurrentLayout(
                    background = dock_color.bg1,
                ),
                Powerline(type='close'),

                widget.Spacer(),
                
                Powerline(type='open'),
                widget.CPU(
                    format = 'CPU {load_percent:2.0f}%',
                    background=dock_color.bg1
                ),
                Powerline(),
                widget.Memory(
                    format = 'MEM {MemPercent:2.0f}%',
                    background=dock_color.bg2
                ),
                Powerline(),
                widget.DF(
                    format = 'SSD {r:.0f}%',
                    visible_on_warn=False,
                    background=dock_color.bg1
                ),
                Powerline(),
                widget.Net(
                    format='Up {down:1.1f}{down_suffix} Down {up:1.1f}{up_suffix}',
                    prefix='M',
                    background=dock_color.bg2,
                    mouse_callbacks = {
                        "Button1": lazy.spawn(wifi_settings)
                    }
                ),
                Powerline(),
                widget.Volume(
                    fmt = 'Vol {}',
                    background=dock_color.bg1
                ),
                Powerline(),
                widget.Backlight(
                    format = 'Bns {percent:.0%}',
                    backlight_name = 'amdgpu_bl1',
                    background=dock_color.bg2,
                ),
                Powerline(),
                widget.Battery(
                    discharge_char = "",
                    unknown_char = "=",
                    format = "Bat {percent:2.0%}{char}",
                    update_interval = 10,
                    background = dock_color.bg1,
                    low_percentage = 0.3,
                    low_foreground = dock_color.text,
                    low_background = dock_color.bg3,
                    mouse_callbacks = {
                        "Button1": dmenu_battery()
                    }
                ),
                Powerline(type='close'),

                widget.Spacer(),

                Powerline(type='open'),
                Touchpad(
                    background = dock_color.bg2,
                    enabled_char = "", 
                ),
                widget.Clock(
                    format="%d.%m.%Y %a %H:%M",
                    background=dock_color.bg2
                ),
                Powerline(),
                widget.TextBox(
                    'Shutdown',
                    background = dock_color.bg3,
                    mouse_callbacks = {
                        'Button1': dmenu_exit()
                    },
                ),
                Powerline(type='close'),
            ],
            24,
            margin = [margin, margin, 0, margin],
            background = transparent,
        ),
        left = HideableGap(margin),
        bottom = HideableGap(margin),

        wallpaper = '~/firewatch.jpeg',
        wallpaper_mode = 'fill',
    ),
]

from libqtile import hook
import os
import subprocess
@hook.subscribe.layout_change
def layout_change(layout, group):
    # script = os.path.expanduser('~/.config/picom/rounded_corners.sh')

    if layout.name == 'Full':
        # subprocess.run([script, 'off'])
        screens[0].top.show(False)
        screens[0].left.show(False)
        screens[0].bottom.show(False)
    else:
        # subprocess.run([script, 'on'])
        screens[0].top.show(True)
        screens[0].left.show(True)
        screens[0].bottom.show(True)

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ],
    **layout_defaults,
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = None

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
