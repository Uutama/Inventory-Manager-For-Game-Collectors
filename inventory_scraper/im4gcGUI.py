try:
    import threading
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox, simpledialog
except ImportError as exc:
    raise ImportError("Tkinter is required for the GUI. Install Python with Tk support.") from exc

from inventory_scraper.scraper import Scraper
from inventory_scraper.storage import LocalStorage


class InventoryGUI:
    def __init__(self) -> None:
        self.storage = LocalStorage()
        self.scraper = Scraper()
        self.inventory = []
        self.root = tk.Tk()
        self.root.title("Inventory Manager")
        self.root.geometry("950x520")
        self._build_ui()
        self.load_inventory()

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        self.listbox = tk.Listbox(left_frame, width=80, height=22, selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        scrollbar = tk.Scrollbar(left_frame, command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        right_frame = tk.Frame(main_frame, padx=10)
        right_frame.pack(side="left", fill="y")

        tk.Button(right_frame, text="Add Game", width=24, command=self.add_game).pack(pady=4)
        tk.Button(right_frame, text="Edit Selected", width=24, command=self.edit_item).pack(pady=4)
        tk.Button(right_frame, text="Delete Selected", width=24, command=self.delete_item).pack(pady=4)
        tk.Button(right_frame, text="Refresh Suggested", width=24, command=self.refresh_price).pack(pady=4)
        tk.Button(right_frame, text="Reload Inventory", width=24, command=self.load_inventory).pack(pady=4)
        tk.Button(right_frame, text="Exit", width=24, command=self.root.quit).pack(pady=20)

        detail_frame = tk.Frame(self.root, padx=10, pady=8)
        detail_frame.pack(fill="both", expand=True)

        tk.Label(detail_frame, text="Selected item details:").pack(anchor="w")
        self.detail_text = tk.Text(detail_frame, height=8, wrap="word", state="disabled")
        self.detail_text.pack(fill="both", expand=True)

    def run(self) -> None:
        self.root.mainloop()

    def load_inventory(self) -> None:
        self.inventory = self.storage.load().get("inventory", [])
        self.listbox.delete(0, tk.END)
        for index, item in enumerate(self.inventory, start=1):
            price = item.get("price")
            price_type = item.get("price_type", item.get("condition", "CIB"))
            price_display = f"${price:.2f} ({price_type})" if isinstance(price, (int, float)) else f"{price} ({price_type})"
            suggested = item.get("suggested_price")
            suggested_display = f"${suggested:.2f}" if isinstance(suggested, (int, float)) else "N/A"
            self.listbox.insert(
                tk.END,
                f"{index}. {item.get('title')} [{item.get('platform')}] {item.get('region', 'NTSC-U')} - Set: {price_display} - Suggested: {suggested_display}",
            )
        self._clear_details()

    def on_select(self, event: tk.Event) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        if len(selection) > 1:
            self._show_multiple_details(selection)
            return
        index = selection[0]
        item = self.inventory[index]
        self._show_details(item)

    def _show_multiple_details(self, selection: tuple[int, ...]) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)
        lines = [f"{len(selection)} items selected:"]
        for index in selection:
            item = self.inventory[index]
            lines.append(
                f"{index + 1}. {item.get('title')} [{item.get('platform')}] - Set: {item.get('price')} - Suggested: {item.get('suggested_price')}"
            )
        self.detail_text.insert(tk.END, "\n".join(lines))
        self.detail_text.config(state="disabled")

    def add_game(self) -> None:
        """Open dialog and scrape with user-selected region preference."""
        selected_data = self._show_add_game_dialog()
        if not selected_data:
            return

        title = selected_data["title"]
        platform = selected_data["platform"]
        condition = selected_data["condition"]
        region = selected_data["region"]

        # Pass region preference to help refine search
        candidates = self.scraper.search_games(title, platform, preferred_region=region)

        if not candidates:
            messagebox.showerror("Not Found", f"No results found for '{title}' on {platform}.")
            return

        if len(candidates) == 1:
            selected_game = candidates[0]
        else:
            selected_game = self._choose_from_multiple_matches(candidates, title)
            if selected_game is None:
                return

        # Check if game already exists in inventory
        existing_index = self._find_existing_inventory(selected_game.get("title"), selected_game.get("platform"))

        if existing_index is not None:
            if messagebox.askyesno(
                "Existing Entry",
                f"'{selected_game.get('title')}' already exists in inventory.\nUpdate with new scraped data?",
                parent=self.root
            ):
                data = selected_game
                data["sale_notes"] = self.inventory[existing_index].get("sale_notes", "")
                data["condition"] = condition
                self._display_price_preview(data)
                data["price"] = self._prompt_price(data.get("suggested_price"))
                self.inventory[existing_index] = data
                messagebox.showinfo("Updated", f"Updated {title} ({platform}).")
            else:
                return
        else:
            data = selected_game
            data["sale_notes"] = ""
            data["condition"] = condition
            self._display_price_preview(data)
            data["price"] = self._prompt_price(data.get("suggested_price"))
            self.inventory.append(data)
            messagebox.showinfo("Saved", f"Saved {title} ({platform}) to inventory.")

        self.storage.save({"inventory": self.inventory})
        self.load_inventory()

    def _show_add_game_dialog(self) -> dict | None:
        """Single dialog with Title, Platform, Condition, and Region inputs."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Game")
        dialog.geometry("640x380")
        dialog.transient(self.root)
        dialog.grab_set()                   # Modal

        result = [None]

        # Title
        tk.Label(dialog, text="Game Title:", font=("Arial", 10, "bold")).pack(anchor="w", padx=25, pady=(20, 5))
        title_entry = tk.Entry(dialog, width=52, font=("Arial", 10))
        title_entry.pack(padx=25, pady=5)
        title_entry.focus_set()

        # Platform
        tk.Label(dialog, text="Platform / Console:", font=("Arial", 10, "bold")).pack(anchor="w", padx=25, pady=(12, 5))
        platform_entry = tk.Entry(dialog, width=52, font=("Arial", 10))
        platform_entry.pack(padx=25, pady=5)

        # Condition
        tk.Label(dialog, text="Condition:", font=("Arial", 10, "bold")).pack(anchor="w", padx=25, pady=(12, 5))
        condition_var = tk.StringVar(value="CIB")
        condition_combo = ttk.Combobox(
            dialog,
            textvariable=condition_var,
            values=["Loose", "CIB", "New"],
            state="readonly",
            width=25,
            font=("Arial", 10)
        )
        condition_combo.pack(padx=25, pady=5)
        condition_combo.current(1)

        # Region
        tk.Label(dialog, text="Region:", font=("Arial", 10, "bold")).pack(anchor="w", padx=25, pady=(12, 5))
        region_var = tk.StringVar(value="NTSC-U")
        region_combo = ttk.Combobox(
            dialog,
            textvariable=region_var,
            values=["NTSC-U", "NTSC-J", "PAL"],
            state="readonly",
            width=25,
            font=("Arial", 10)
        )
        region_combo.pack(padx=25, pady=5)
        region_combo.current(0)   # Default to NTSC-U

        def on_ok():
            title = title_entry.get().strip()
            platform = platform_entry.get().strip()
            condition = condition_var.get()
            region = region_var.get()

            if not title:
                messagebox.showwarning("Missing Title", "Please enter a game title.", parent=dialog)
                title_entry.focus_set()
                return
            if not platform:
                messagebox.showwarning("Missing Platform", "Please enter a platform.", parent=dialog)
                platform_entry.focus_set()
                return

            result[0] = {
                "title": title,
                "platform": platform,
                "condition": condition,
                "region": region
            }
            dialog.destroy()

        def on_cancel():
            result[0] = None
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=25)

        tk.Button(button_frame, text="Add Game", width=14, command=on_ok).pack(side="left", padx=12)
        tk.Button(button_frame, text="Cancel", width=14, command=on_cancel).pack(side="left", padx=12)

        # Keyboard support
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self.root.wait_window(dialog)
        return result[0]

    def edit_item(self) -> None:
        selected_items = self._get_selected_items()
        if not selected_items:
            messagebox.showwarning("Select item", "Please select an item to edit.")
            return

        if len(selected_items) > 1:
            if not messagebox.askyesno(
                "Edit Multiple Items",
                f"Edit {len(selected_items)} selected items with the same price and notes?",
                parent=self.root,
            ):
                return

            new_price = simpledialog.askstring(
                "Edit Price",
                "Press Enter to keep current prices for each item.\nOr enter a new set price to apply to all selected items:",
                parent=self.root,
            )
            if new_price is not None and new_price.strip() != "":
                try:
                    updated_price = float(new_price.strip())
                    for _, item in selected_items:
                        item["price"] = updated_price
                except ValueError:
                    messagebox.showwarning("Invalid value", "Price must be a number. Keeping current prices.")

            sale_notes = simpledialog.askstring(
                "Sales Notes",
                "Sales notes to apply to all selected items:",
                parent=self.root,
            )
            if sale_notes is not None:
                for _, item in selected_items:
                    item["sale_notes"] = sale_notes

            self.storage.save({"inventory": self.inventory})
            self.load_inventory()
            messagebox.showinfo("Updated", "Selected inventory items updated.")
            return

        index, item = selected_items[0]
        current_price = item.get("price")
        new_price = simpledialog.askstring(
            "Edit Price",
            f"Press Enter to keep current price ({current_price}).\nOr enter new set price:",
            parent=self.root,
        )
        if new_price is not None and new_price.strip() != "":
            try:
                item["price"] = float(new_price.strip())
            except ValueError:
                messagebox.showwarning("Invalid value", "Price must be a number. Keeping current price.")

        available_types = self._get_available_price_types(item)
        if available_types:
            chosen_type = self._prompt_price_type(item.get("price_type", item.get("condition", "CIB")), available_types)
            if chosen_type:
                item["price_type"] = chosen_type
                item["price"] = available_types[chosen_type]

        sale_notes = simpledialog.askstring(
            "Sales Notes",
            "Sales notes:",
            initialvalue=item.get("sale_notes", ""),
            parent=self.root,
        )
        if sale_notes is not None:
            item["sale_notes"] = sale_notes
        self.storage.save({"inventory": self.inventory})
        self.load_inventory()
        self.listbox.select_set(index)
        self.on_select(None)
        messagebox.showinfo("Updated", "Inventory item updated.")

    def delete_item(self) -> None:
        selected_items = self._get_selected_items()
        if not selected_items:
            messagebox.showwarning("Select item", "Please select an item to delete.")
            return

        if len(selected_items) > 1:
            item_count = len(selected_items)
            if not messagebox.askyesno(
                "Delete Selected",
                f"Delete {item_count} selected items?",
                parent=self.root,
            ):
                return
            for index, _ in sorted(selected_items, key=lambda pair: pair[0], reverse=True):
                self.inventory.pop(index)
            self.storage.save({"inventory": self.inventory})
            self.load_inventory()
            return

        index, item = selected_items[0]
        if not messagebox.askyesno("Delete item", f"Delete {item.get('title')} ({item.get('platform')})?", parent=self.root):
            return
        self.inventory.pop(index)
        self.storage.save({"inventory": self.inventory})
        self.load_inventory()

    def refresh_price(self) -> None:
        selected = self._get_selected_item()
        if selected is None:
            messagebox.showwarning("Select item", "Please select an item to refresh.")
            return
        index, item = selected
        condition = item.get("condition", item.get("price_type", "CIB"))
        updated = self.scraper.fetch_game_data(item["title"], item["platform"], condition)
        item["suggested_price"] = updated.get("suggested_price")
        item["sale_info"] = updated.get("sale_info", item.get("sale_info", ""))
        item["scraped_at"] = updated.get("scraped_at")
        item["scraped_data"] = updated.get("scraped_data", item.get("scraped_data", {}))
        item["price_type"] = updated.get("price_type", item.get("price_type", item.get("condition", "CIB")))
        item["condition"] = updated.get("condition", item.get("condition", item.get("price_type", "CIB")))
        self.storage.save({"inventory": self.inventory})
        self.load_inventory()
        self.listbox.select_set(index)
        self.on_select(None)
        messagebox.showinfo(
            "Refreshed",
            f"Suggested price refreshed to {item.get('suggested_price')} for {item.get('title')}.",
        )

    def _get_selected_item(self) -> tuple[int, dict] | None:
        selected = self._get_selected_items()
        return selected[0] if selected else None

    def _get_selected_items(self) -> list[tuple[int, dict]]:
        indices = self.listbox.curselection()
        return [(index, self.inventory[index]) for index in indices]

    def _choose_from_multiple_matches(self, candidates: list[dict], title: str) -> dict | None:
        """Improved dialog with Listbox for selecting from multiple matches."""
        if not candidates:
            return None

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Multiple Matches Found - {title}")
        dialog.geometry("700x480")
        dialog.transient(self.root)
        dialog.grab_set()          # Modal dialog

        # Instructions
        tk.Label(
            dialog,
            text=f"Found {len(candidates)} possible matches for:\n'{title}'",
            font=("Arial", 11, "bold")
        ).pack(pady=(15, 5))

        tk.Label(dialog, text="Select the correct game:").pack(anchor="w", padx=20)

        # Create Listbox with scrollbar
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=8)

        self.match_listbox = tk.Listbox(
            list_frame,
            height=18,
            font=("Arial", 10),
            selectmode="single"
        )
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.match_listbox.yview)
        
        self.match_listbox.config(yscrollcommand=scrollbar.set)

        self.match_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Populate the Listbox with rich information
        for i, item in enumerate(candidates, 1):
            region = item.get("region", "NTSC-U")
            score = item.get("match_score", "?")
            suggested = item.get("suggested_price")
            suggested_str = f"${suggested:.2f}" if isinstance(suggested, (int, float)) else "N/A"

            cib = item.get("scraped_data", {}).get("complete_price") or item.get("complete_price")
            loose = item.get("scraped_data", {}).get("loose_price") or item.get("loose_price")

            display_text = (
                f"{i:2d}. {item.get('title')}  [{region}]   "
                f"Score: {score}%   "
                f"Suggested: {suggested_str}   "
                f"CIB: ${cib or 'N/A'}   Loose: ${loose or 'N/A'}"
            )
            self.match_listbox.insert(tk.END, display_text)

        # Double-click to select
        self.match_listbox.bind("<Double-Button-1>", lambda e: self._on_match_selected(dialog, candidates))

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=12)

        tk.Button(
            button_frame,
            text="Select",
            width=12,
            command=lambda: self._on_match_selected(dialog, candidates)
        ).pack(side="left", padx=8)

        tk.Button(
            button_frame,
            text="Cancel",
            width=12,
            command=dialog.destroy
        ).pack(side="left", padx=8)

        # Keyboard support
        dialog.bind("<Return>", lambda e: self._on_match_selected(dialog, candidates))
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self.root.wait_window(dialog)

        # Return the selected item (set by _on_match_selected)
        return getattr(self, "_selected_match", None)

    def _on_match_selected(self, dialog: tk.Toplevel, candidates: list[dict]):
        """Helper to handle selection from Listbox."""
        selection = self.match_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a game.", parent=dialog)
            return

        index = selection[0]
        self._selected_match = candidates[index]
        dialog.destroy()

    def _show_details(self, item: dict) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)
        details = [
            f"Title: {item.get('title')}",
            f"Region: {item.get('region', 'NTSC-U')}",
            f"Platform: {item.get('platform')}",
            f"Condition: {item.get('condition', item.get('price_type', 'CIB'))}",
            f"Set price: {item.get('price')}",
            f"Suggested price: {item.get('suggested_price')}",
            f"Price type: {item.get('price_type', item.get('condition', 'CIB'))}",
        ]

        parsed = self._get_available_price_types(item)
        if parsed:
            details.append("Available parsed prices:")
            for label, value in parsed.items():
                details.append(f"  {label}: ${value:.2f}")

        details.extend([
            f"Sale info: {item.get('sale_info', '')}",
            f"Sales notes: {item.get('sale_notes', '')}",
            f"Scraped at: {item.get('scraped_at', 'N/A')}",
        ])
        self.detail_text.insert(tk.END, "\n".join(details))
        self.detail_text.config(state="disabled")

    def _display_price_preview(self, item: dict) -> None:
        suggested_price = item.get("suggested_price")
        price_type = item.get("price_type", item.get("condition", "CIB"))
        if isinstance(suggested_price, (int, float)):
            message = f"Suggested price: ${suggested_price:.2f} ({price_type})"
        else:
            message = "Suggested price: N/A"
        if item.get("sale_info"):
            message += f"\nNotes: {item.get('sale_info')}"
        messagebox.showinfo("Price Preview", message)

    def _clear_details(self) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.config(state="disabled")

    def _prompt_condition(self) -> str | None:
        """Show a clean dropdown dialog to select condition."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Condition")
        dialog.geometry("300x180")
        dialog.transient(self.root)        # Make it a child window
        dialog.grab_set()                  # Make it modal

        tk.Label(dialog, text="Choose game condition:", font=("Arial", 10)).pack(pady=15)

        condition_var = tk.StringVar(value="CIB")

        combo = ttk.Combobox(
            dialog,
            textvariable=condition_var,
            values=["Loose", "CIB", "New"],
            state="readonly",          # Prevents typing
            width=25,
            font=("Arial", 10)
        )
        combo.pack(pady=8)
        combo.current(1)               # Default to CIB (index 1)
        combo.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        result = [None]  # Use list to modify inside nested function

        def on_ok():
            result[0] = condition_var.get()
            dialog.destroy()

        def on_cancel():
            result[0] = None
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=8)
        tk.Button(button_frame, text="Cancel", width=10, command=on_cancel).pack(side="left", padx=8)

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self.root.wait_window(dialog)
        return result[0]

    def _prompt_price(self, suggested: float | None) -> float | None:
        if suggested is None:
            return simpledialog.askfloat("Set Price", "Enter the price:", parent=self.root)
        use_suggested = messagebox.askyesno(
            "Suggested price",
            f"Suggested price: ${suggested:.2f}.\nUse suggested price?",
            parent=self.root,
        )
        if use_suggested:
            return suggested
        return simpledialog.askfloat("Set Price", "Enter the price:", parent=self.root)

    def _get_available_price_types(self, item: dict) -> dict[str, float]:
        scraped_data = item.get("scraped_data", {}) or {}
        return {
            label: scraped_data[key]
            for label, key in (
                ("CIB", "complete_price"),
                ("Loose", "loose_price"),
                ("New", "new_price"),
            )
            if scraped_data.get(key) is not None
        }

    def _prompt_price_type(self, current_type: str, available_types: dict[str, float]) -> str | None:
        if not available_types:
            return None
        options = ", ".join(available_types.keys())
        raw = simpledialog.askstring(
            "Price Type",
            f"Choose price type [{options}] (current: {current_type}):",
            parent=self.root,
        )
        if raw is None or raw.strip() == "":
            return None
        normalized = raw.strip().title()
        if normalized not in available_types:
            messagebox.showwarning(
                "Invalid value",
                "Invalid or unavailable price type. Keeping current type.",
                parent=self.root,
            )
            return None
        return normalized

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

