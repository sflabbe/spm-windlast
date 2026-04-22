from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModuleSelection:
    include: bool = False


@dataclass
class ReportSelection:
    windlast: ModuleSelection = field(default_factory=lambda: ModuleSelection(True))
    verankerung: ModuleSelection = field(default_factory=ModuleSelection)
    herstellernachweis: ModuleSelection = field(default_factory=ModuleSelection)

    def selected_module_labels(self) -> list[str]:
        labels = []
        if self.windlast.include:
            labels.append("Windlast")
        if self.verankerung.include:
            labels.append("Verankerung")
        if self.herstellernachweis.include:
            labels.append("Herstellernachweis")
        return labels
