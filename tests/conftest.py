"""pytest-Konfiguration.

Verhindert, dass pytest den ``_legacy/``-Ordner mit den historischen
flachen Modulen als Testverzeichnis einsammelt.
"""

collect_ignore_glob = ["_legacy/*"]
