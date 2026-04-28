import json
import csv
from pathlib import Path
from typing import Any


class LocalStorage:
    def __init__(self, path: str = "inventory_data.json") -> None:
        self.path = Path(path)
        self.csv_path = self.path.with_suffix(".csv")   # inventory_data.csv
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, data: Any) -> None:
        """Save inventory to JSON and automatically generate a clean CSV file."""
        # Save the main JSON file (used by the GUI)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Auto-generate/update the CSV file for easy viewing in Excel/Google Sheets
        self._save_to_csv(data)

    def load(self) -> Any:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_to_csv(self, data: Any) -> None:
        """Convert inventory to a clean, readable CSV with a Region column."""
        inventory = data.get("inventory", [])
        
        if not inventory:
            # Create empty CSV with headers
            headers = ["Title", "Platform", "Region", "Condition", "Set_Price", 
                      "Suggested_Price", "Loose_Price", "CIB_Price", "New_Price", 
                      "Price_Type", "Sale_Notes", "Scraped_At"]
            self.csv_path.write_text(",".join(headers) + "\n", encoding="utf-8")
            return

        headers = [
            "Title", "Platform", "Region", "Condition", "Set_Price",
            "Suggested_Price", "Loose_Price", "CIB_Price", "New_Price",
            "Price_Type", "Sale_Notes", "Scraped_At"
        ]

        rows = []
        for item in inventory:
            scraped = item.get("scraped_data", {}) or {}

            row = {
                "Title": item.get("title", ""),
                "Platform": item.get("platform", ""),
                "Region": item.get("region", ""),                    # ← New column
                "Condition": item.get("condition", item.get("price_type", "CIB")),
                "Set_Price": item.get("price", ""),
                "Suggested_Price": item.get("suggested_price", ""),
                "Loose_Price": scraped.get("loose_price", ""),
                "CIB_Price": scraped.get("complete_price", ""),
                "New_Price": scraped.get("new_price", ""),
                "Price_Type": item.get("price_type", item.get("condition", "")),
                "Sale_Notes": str(item.get("sale_notes", "")).replace("\n", " | "),
                "Scraped_At": item.get("scraped_at", ""),
            }
            rows.append(row)

        # Write CSV file
        try:
            with self.csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            print(f"Warning: Could not write CSV file: {e}")

        # Optional: Print confirmation (you can remove this later)
        print(f"✅ Inventory saved. CSV updated → {self.csv_path.name}")