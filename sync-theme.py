#!/usr/bin/env python3
"""Pin monitor configs to Omarchy's palette; reload btop only on changes."""

import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Follow a user-owned config symlink instead of replacing it.
    destination = path.resolve() if path.is_symlink() else path
    mode = destination.stat().st_mode & 0o777 if destination.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".theme-sync-", dir=destination.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def pin_config(path, settings, backup):
    original = path.read_text() if path.exists() else ""
    updated = original
    for key, value in settings.items():
        pattern = rf"(?m)^[ \t]*{re.escape(key)}[ \t]*=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, updated):
            updated = re.sub(pattern, replacement, updated)
        else:
            updated = updated.rstrip("\n") + ("\n" if updated else "") + replacement + "\n"
    if updated == original:
        return False
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    atomic_write(path, updated)
    return True


def pin_theme(path, source, backup):
    if path.is_symlink() and os.readlink(path) == str(source):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    # Replace only our dedicated theme file, keeping other installed themes.
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    try:
        temporary.symlink_to(source)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def main():
    home = Path.home()
    source = home / ".local/state/omarchy/current/theme/btop.theme"
    try:
        palette = source.read_bytes()
    except FileNotFoundError:
        # Omarchy briefly removes current/theme while swapping themes.
        return
    if b"theme[main_fg]" not in palette:
        raise ValueError(f"Not a monitor theme: {source}")

    state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state")) / "omarchy/system-monitor-theme"
    state.mkdir(parents=True, exist_ok=True)
    with (state / "sync.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        digest = hashlib.sha256(palette).hexdigest() + "\n"
        stamp = state / "palette.sha256"
        changed = not stamp.exists() or stamp.read_text() != digest
        btop = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "btop"
        # bpytop 1.0.68 explicitly uses ~/.config, rather than XDG_CONFIG_HOME.
        bpytop = home / ".config/bpytop"
        for app, folder, theme in (("btop", btop, "omarchy-system"),
                                   ("bpytop", bpytop, "+omarchy-system")):
            link_changed = pin_theme(folder / "themes/omarchy-system.theme", source,
                                     state / f"{app}-theme.before-sync")
            settings = {"color_theme": f'"{theme}"', "truecolor": "true" if app == "btop" else "True"}
            if app == "btop":
                settings["force_tty"] = "false"
            config_changed = pin_config(folder / f"{app}.conf", settings,
                                        state / f"{app}.conf.before-sync")
            if app == "btop" and (changed or link_changed or config_changed):
                # bpytop has no reload signal; SIGUSR2 would terminate it.
                subprocess.run(["pkill", "-u", str(os.getuid()), "-x", "-SIGUSR2", "btop"],
                               check=False, stdout=subprocess.DEVNULL)
        if changed:
            atomic_write(stamp, digest)


if __name__ == "__main__":
    main()
