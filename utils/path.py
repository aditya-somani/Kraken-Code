from pathlib import Path

def resolve_path(base: str | Path, path: str | Path) -> Path:
    """
    Resolves a path relative to a base directory.
    
    Args:
        base: The base directory.
        path: The path to resolve.
    
    Returns:
        The resolved path.
    """
    path = Path(path)
    if path.is_absolute():
        return path.resolve()
    return base.resolve() / path # ex: base = /home/user, path = /etc/passwd -> /home/user/etc/passwd

def is_binary_file(path: str | Path) -> bool:
    """
    Checks if a file is binary.
    
    Args:
        path: The path to the file.
    
    Returns:
        True if the file is binary, False otherwise.
    """
    try:
        with open(path, 'rb') as f:
            chunk = f.read(8192)
            return b'\x00' in chunk # "\x00" is a null byte, if it is present in the file, it is a binary file.
    except Exception:
        return False