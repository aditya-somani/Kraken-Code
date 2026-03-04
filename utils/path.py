from pathlib import Path

def resolve_path(base: str | Path, path: str | Path) -> Path:
    """
    Resolves a path relative to a base directory.
    
    Args:
        base: The base directory (usually the working directory - cwd).
        path: The path to resolve i.e. file name or directory name or relative path.
    
    Returns:
        The resolved path.
    """
    path = Path(path)
    if path.is_absolute():
        return path.resolve()
    return base.resolve() / path # ex: base = /home/user, path = /etc/passwd -> /home/user/etc/passwd

def display_path_rel_to_cwd(path: str, cwd: Path | None) -> str:
    """
    Displays a path relative to the current working directory.
    
    Args:
        path: The path to display.
        cwd: The current working directory.
    """
    # This function will be changed in the future, it's good enough for now.
    try:
        p = Path(path)
    except Exception:
        return path

    if cwd:
        try:
            return str(p.relative_to(cwd))
        except ValueError:
            pass
    
    return str(p)

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