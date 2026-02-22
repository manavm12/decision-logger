"""Shell history setup utilities"""

from pathlib import Path


def enable_extended_history() -> bool:
    """
    Auto-enable zsh extended history by adding to ~/.zshrc

    Returns:
        True if enabled successfully or already enabled, False otherwise
    """
    zshrc = Path.home() / '.zshrc'

    # Check if already enabled
    if zshrc.exists():
        try:
            content = zshrc.read_text()
            if 'EXTENDED_HISTORY' in content:
                return True  # Already enabled
        except Exception:
            pass

    # Add configuration
    config_lines = [
        "\n# Enable extended history for decision-logger",
        "setopt EXTENDED_HISTORY",
        "setopt INC_APPEND_HISTORY",
        "setopt HIST_FIND_NO_DUPS\n"
    ]

    try:
        with open(zshrc, 'a') as f:
            f.write('\n'.join(config_lines))
        return True
    except Exception:
        return False


def check_extended_history_enabled() -> bool:
    """
    Check if extended history is currently enabled.

    Returns:
        True if extended history is enabled in ~/.zshrc
    """
    zshrc = Path.home() / '.zshrc'

    if not zshrc.exists():
        return False

    try:
        content = zshrc.read_text()
        return 'EXTENDED_HISTORY' in content
    except Exception:
        return False
