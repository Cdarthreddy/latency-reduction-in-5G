"""
Console output utilities with Windows encoding support.
"""
import sys


def safe_print(message: str, fallback: str | None = None) -> None:
    """ 
    Args:
        message: Message to print (may contain Unicode characters)
        fallback: Fallback message if encoding fails (default: strip emojis)
    """
    try:
        print(message)
    except UnicodeEncodeError:
        if fallback:
            print(fallback)
        else:
            # Remove common emoji characters
            fallback_msg = message
            emoji_replacements = {
                '[OK]': '[OK]',
                '[WARN]': '[WARN]',
                '[START]': '[START]',
                '[UPLOAD]': '[UPLOAD]',
                '[SAVE]': '[SAVE]',
                '[LOAD]': '[LOAD]',
                '-\u003e': '-\u003e',
                '[CONFIG]': '[CONFIG]',
            }
            for emoji, replacement in emoji_replacements.items():
                fallback_msg = fallback_msg.replace(emoji, replacement)
            print(fallback_msg)


def setup_console_encoding():
    """Setup console encoding to support UTF-8 if possible."""
    if sys.platform == 'win32':
        try:
            # Try to set UTF-8 encoding
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            # If that fails, just use safe_print for all output
            pass

