from __future__ import annotations

from datetime import datetime

from inventory_scraper.scraper import Scraper
from inventory_scraper.storage import LocalStorage


class InventoryManager:
    def __init__(self) -> None:
        self.storage = LocalStorage()
        self.scraper = Scraper()
        self.inventory = self.storage.load().get("inventory", [])
        self.mainmenu = False

    def run(self) -> None:
        while True:
            print("\n\nInventory Manager")
            if not self.mainmenu:
                print("--- Please select a condition ---")
                self.mainmenu = True
            print("1. Add game to inventory")
            print("2. Show inventory")
            print("3. Edit inventory item")
            print("4. Delete inventory item")
            print("5. Refresh suggested price")
            print("0. Exit")
            print("-----------------------------")
            choice = input("Select an option: ").strip()
            if choice == "1":
                self.add_game()
            elif choice == "2":
                self.show_inventory()
            elif choice == "3":
                self.edit_inventory()
            elif choice == "4":
                self.delete_inventory()
            elif choice == "5":
                self.refresh_suggested_price()
            elif choice == "0":
                print("Exiting inventory manager.")
                break
            else:
                print("Invalid selection. Please choose a valid option.")

    def add_game(self) -> None:
        title = input("\nGame title: ").strip()
        platform = input("Platform: ").strip()
        condition = self._prompt_condition()
        existing_index = self._find_existing_inventory(title, platform)
        if existing_index is not None:
            existing_item = self.inventory[existing_index]
            scraped_at = existing_item.get("scraped_at")
            if scraped_at:
                formatted_date = self._format_scraped_date(scraped_at)
                print(f"Pricing data found from {formatted_date}. Use existing data, or search for updated data?")
            else:
                print("Pricing data found locally. Use existing data, or search for updated data?")
            print(f"Requested condition: {condition}")
            self._display_price_preview(existing_item)
            if self._confirm("Use existing data?"):
                print("Keeping existing inventory item.")
                return
            print("Refreshing the saved data from PriceCharting and updating this item...")
            data = self.scraper.fetch_game_data(title, platform, condition)
            data["sale_notes"] = existing_item.get("sale_notes", "")
            data["condition"] = condition
            self._display_price_preview(data)
            data["price"] = self._prompt_price("Set price", data.get("suggested_price"))
            self.inventory[existing_index] = data
            self.save_inventory()
            print(f"Updated {title} ({platform}) in inventory with refreshed scrape.")
            return

        data = self.scraper.fetch_game_data(title, platform, condition)
        data["sale_notes"] = ""
        data["condition"] = condition
        self._display_price_preview(data)
        data["price"] = self._prompt_price("Set price", data.get("suggested_price"))
        self.inventory.append(data)
        self.save_inventory()
        print(f"Saved {title} ({platform}) to inventory.")

    def show_inventory(self) -> None:
        if not self.inventory:
            print("No inventory items saved.")
            return
        for index, item in enumerate(self.inventory, start=1):
            current_price = item.get("price")
            price_type = item.get("price_type", "CIB")
            suggested_price = item.get("suggested_price")
            price_label = (
                f"${current_price:.2f} ({price_type})"
                if isinstance(current_price, (int, float))
                else f"{current_price} ({price_type})"
            )
            suggested_label = f"${suggested_price:.2f}" if isinstance(suggested_price, (int, float)) else suggested_price or "N/A"
            sale_info = item.get("sale_info", "")
            sale_notes = item.get("sale_notes", "")
            scraped_at = item.get("scraped_at")
            metadata_parts = [part for part in [sale_info, sale_notes] if part]
            metadata = "; ".join(metadata_parts) if metadata_parts else ""
            if scraped_at:
                metadata = f"{metadata} (scraped: {scraped_at})" if metadata else f"Scraped: {scraped_at}"
            print(
                f"#{index}: {item['title']} - {item['platform']} - Set price: {price_label} - Suggested price: {suggested_label} - {metadata}"
            )

    def edit_inventory(self) -> None:
        if not self.inventory:
            print("No inventory items saved.")
            return
        self.show_inventory()
        selection = input("Enter the item number to edit: ").strip()
        if not selection.isdigit() or int(selection) < 1 or int(selection) > len(self.inventory):
            print("Invalid item number.")
            return
        index = int(selection) - 1
        item = self.inventory[index]
        print("Press Enter to keep the current value.")
        current_price = item.get("price")
        current_type = item.get("price_type", "CIB")
        print(f"Current set price: {current_price} ({current_type})")
        available_types = self._get_available_price_types(item)
        if available_types:
            print("Available parsed price variants:")
            for label, value in available_types.items():
                print(f"  {label}: ${value:.2f}")
            chosen_type = self._prompt_price_type(current_type, available_types)
            if chosen_type:
                item["price"] = available_types[chosen_type]
                item["price_type"] = chosen_type
        else:
            print("No parsed price variants available; keeping current price type.")
        item["sale_notes"] = self._prompt_text("Sales notes", item.get("sale_notes", ""))
        self.save_inventory()
        print("Inventory item updated.")

    def refresh_suggested_price(self) -> None:
        if not self.inventory:
            print("No inventory items saved.")
            return
        self.show_inventory()
        selection = input("Enter the item number to refresh suggested price: ").strip()
        if not selection.isdigit() or int(selection) < 1 or int(selection) > len(self.inventory):
            print("Invalid item number.")
            return
        index = int(selection) - 1
        item = self.inventory[index]
        print(f"Refreshing suggested price for {item['title']} ({item['platform']})...")
        updated = self.scraper.fetch_game_data(item["title"], item["platform"])
        old_suggested = item.get("suggested_price")
        item["suggested_price"] = updated.get("suggested_price")
        item["sale_info"] = updated.get("sale_info", item.get("sale_info", ""))
        item["scraped_at"] = updated.get("scraped_at")
        item["scraped_data"] = updated.get("scraped_data", item.get("scraped_data", {}))
        self.save_inventory()
        print(
            f"Suggested price updated from {old_suggested} to {item.get('suggested_price')} for {item['title']} ({item['platform']})."
        )
        
    def delete_inventory(self) -> None:
        if not self.inventory:
            print("No inventory items saved.")
            return
        self.show_inventory()
        selection = input("Enter the item number(s) or title to delete: ").strip()
        if not selection:
            print("No selection entered.")
            return

        if self._is_number_list(selection):
            indices = self._parse_item_numbers(selection)
            if not indices:
                print("Invalid item number selection.")
                return
            deleted_items = []
            for index in sorted(indices, reverse=True):
                if index < 0 or index >= len(self.inventory):
                    print(f"Invalid item number: {index + 1}.")
                    return
                deleted_items.append(self.inventory.pop(index))
            self.save_inventory()
            for item in reversed(deleted_items):
                print(f"Deleted inventory item: {item['title']} ({item['platform']}).")
            return

        matches = [
            (index, item)
            for index, item in enumerate(self.inventory)
            if item.get("title", "").lower() == selection.lower()
        ]
        if not matches:
            print("No inventory item found with that title. Please enter the exact title or use the item number(s).")
            return
        if len(matches) > 1:
            self._print_multiple_matches(matches)
            match_selection = input("Enter the matching item number to delete, or press Enter to cancel: ").strip()
            if not match_selection:
                print("Delete canceled.")
                return
            if not match_selection.isdigit():
                print("Invalid selection.")
                return
            index = int(match_selection) - 1
            if index < 0 or index >= len(self.inventory):
                print("Invalid item number.")
                return
            deleted_item = self.inventory[index]
        else:
            deleted_item = matches[0][1]

        if not self._confirm(f"Delete {deleted_item['title']} ({deleted_item['platform']})?"):
            print("Delete canceled.")
            return
        self.inventory.remove(deleted_item)
        self.save_inventory()
        print(f"Deleted inventory item: {deleted_item['title']} ({deleted_item['platform']}).")

    def _parse_item_numbers(self, selection: str) -> list[int]:
        parts = [part.strip() for part in selection.split(",") if part.strip()]
        indices = []
        for part in parts:
            if not part.isdigit():
                return []
            indices.append(int(part) - 1)
        return sorted(set(indices))

    def _is_number_list(self, selection: str) -> bool:
        parts = [part.strip() for part in selection.split(",") if part.strip()]
        return bool(parts) and all(part.isdigit() for part in parts)

    def _print_multiple_matches(self, matches: list[tuple[int, dict]]) -> None:
        print("Matching inventory items:")
        for index, item in matches:
            current_price = item.get("price")
            price_type = item.get("price_type", "CIB")
            suggested_price = item.get("suggested_price")
            price_label = (
                f"${current_price:.2f} ({price_type})"
                if isinstance(current_price, (int, float))
                else f"{current_price} ({price_type})"
            )
            suggested_label = f"${suggested_price:.2f}" if isinstance(suggested_price, (int, float)) else suggested_price or "N/A"
            print(
                f"#{index + 1}: {item['title']} - {item['platform']} - Set price: {price_label} - Suggested price: {suggested_label}"
            )

    def _confirm(self, message: str) -> bool:
        response = input(f"{message} (y/n): ").strip().lower()
        return response in {"y", "yes"}

    def _prompt_text(self, label: str, current: str) -> str:
        value = input(f"{label} [{current}]: ").strip()
        return value if value else current

    def _prompt_float(self, label: str, current):
        current_label = f"{current}" if current is not None else ""
        raw = input(f"{label} [{current_label}]: ").strip()
        if raw == "":
            return current
        try:
            return float(raw)
        except ValueError:
            print("Invalid number entered. Keeping current value.")
            return current

    def _prompt_price(self, label: str, default: float | None):
        default_label = f"{default}" if default is not None else ""
        raw = input(f"""Press Enter to use Suggested Price, or add your own [{default_label}]: """).strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            print("Invalid number entered. Using suggested price.")
            return default

    def _prompt_condition(self) -> str:
        while True:
            raw = input("Condition ('L' for Loose, 'C' for CIB, 'N' for New): ").strip().lower()
            if raw in {"l", "loose"}:
                return "Loose"
            if raw in {"c", "cib"}:
                return "CIB"
            if raw in {"n", "new"}:
                return "New"
            print("Invalid condition. Please enter L, C, N, Loose, CIB, or New.")

    def _display_price_preview(self, item: dict) -> None:
        suggested_price = item.get("suggested_price")
        price_type = item.get("price_type", item.get("condition", "CIB"))
        if isinstance(suggested_price, (int, float)):
            print(f"Suggested price: ${suggested_price:.2f} ({price_type})")
        else:
            print("Suggested price: N/A")
        if item.get("sale_info"):
            print(f"Notes: {item.get('sale_info')}")

    def _format_scraped_date(self, scraped_at: str) -> str:
        try:
            parsed = datetime.fromisoformat(scraped_at.replace("Z", ""))
            return parsed.strftime("%m-%d-%Y")
        except ValueError:
            return scraped_at

    def _find_existing_inventory(self, title: str, platform: str) -> int | None:
        normalized_title = title.strip().lower()
        normalized_platform = platform.strip().lower()
        for index, item in enumerate(self.inventory):
            if (
                item.get("title", "").strip().lower() == normalized_title
                and item.get("platform", "").strip().lower() == normalized_platform
            ):
                return index
        return None

    def _get_available_price_types(self, item: dict) -> dict[str, float]:
        scraped_data = item.get("scraped_data", {}) or {}
        return {
            label: scraped_data[key]
            for label, key in (("CIB", "complete_price"), ("Loose", "loose_price"), ("New", "new_price"))
            if scraped_data.get(key) is not None
        }

    def _prompt_price_type(self, current_type: str, available_types: dict[str, float]) -> str | None:
        raw = input(f"Choose price type [CIB/Loose/New] (current: {current_type}): ").strip()
        if raw == "":
            return None
        normalized = raw.title()
        if normalized not in available_types:
            print("Invalid or unavailable price type. Keeping current price type.")
            return None
        return normalized

    def save_inventory(self) -> None:
        self.storage.save({"inventory": self.inventory})
