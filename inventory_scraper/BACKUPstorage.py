import json
from pathlib import Path
from typing import Any


class LocalStorage:
    def __init__(self, path: str = "inventory_data.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, data: Any) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> Any:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
