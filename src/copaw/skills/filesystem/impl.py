from pathlib import Path


def read_file(path: str, encoding: str = "utf-8") -> str:
    """Read a text file and return its contents."""
    return Path(path).read_text(encoding=encoding)


def write_file(
    path: str,
    content: str,
    mode: str = "replace",
    encoding: str = "utf-8",
) -> str:
    """Write text to a file, supporting append or replace."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        with p.open("a", encoding=encoding) as f:
            f.write(content)
    else:
        p.write_text(content, encoding=encoding)
    return f"written {len(content)} chars"


def list_dir(path: str, recursive: bool = False) -> list[str]:
    """List directory contents, optionally recursively."""
    p = Path(path)
    if not p.exists():
        return []
    if recursive:
        return [str(x) for x in p.rglob("*")]
    return [str(x) for x in p.iterdir()]
