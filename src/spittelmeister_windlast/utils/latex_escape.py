"""LaTeX-Escape-Helfer fuer benutzerdefinierte Strings (Projektname, Adresse...)."""

from __future__ import annotations

import re

_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

_PATTERN = re.compile(r"[\\&%$#_{}\~\^]")


def latex_escape(text: object) -> str:
    """Escape der LaTeX-Metazeichen in einem String.

    Uebergabe von None ergibt einen leeren String. Nicht-Strings werden per
    `str()` konvertiert, damit Zahlen direkt in Templates genutzt werden koennen.
    """
    if text is None:
        return ""
    return _PATTERN.sub(lambda m: _MAP[m.group()], str(text))


__all__ = ["latex_escape"]
