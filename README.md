# Robbie-Btop-Theming

A background Omarchy shell plugin that pins **btop** and **bpytop** to the
current system theme. It runs silently with no tray icon or bar widget, and
starts automatically with the Omarchy shell after reboot when enabled.

> **bpytop needs a restart:** after changing your system theme, close and reopen
> bpytop to apply the new colors. It does not support live theme reloads.
> btop reloads automatically.

## Installation

Requires Omarchy with shell plugin support, Python 3, and `pkill` (procps-ng).
Install btop and/or bpytop separately if needed.

```sh
omarchy plugin add https://github.com/RobbieUK1/Robbie-Btop-Theming --enable
```

## Features

- Runs on shell startup and checks every three seconds.
- Uses Omarchy's current `btop.theme`, compatible with both monitors.
- Creates `themes/omarchy-system.theme` in each app's configuration directory.
- Enforces `color_theme` and truecolor, and disables btop's forced TTY palette.
- Preserves other settings, including background transparency.
- Reloads running btop instances after palette or configuration changes.
- bpytop does not support live configuration reloads: reopen it after switching
  the system theme. Settings it saves on exit are corrected on the next check.

## Controls

```sh
omarchy plugin enable robbie.system-monitor-theme
omarchy plugin disable robbie.system-monitor-theme
omarchy-shell system-monitor-theme sync
```

Disabling stops enforcement; the last selected theme remains configured.
Original existing configuration files are backed up before the first change to
`~/.local/state/omarchy/system-monitor-theme/<app>.conf.before-sync`
(or under `$XDG_STATE_HOME` when set). Disable the plugin before restoring a backup.

The helper can also be run directly:

```sh
python3 ~/.config/omarchy/plugins/robbie.system-monitor-theme/sync-theme.py
```
