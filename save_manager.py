"""
Save and Profile Manager for CYBER NOVA: ODYSSEY.
Supports:
- Profile stats and high scores
- 5 Distinct Save File Slots:
    - Slot 1: Auto-Save Slot (auto_save)
    - Slot 2: Manual Save 1 (manual_1)
    - Slot 3: Manual Save 2 (manual_2)
    - Slot 4: Manual Save 3 (manual_3)
    - Slot 5: Manual Save 4 (manual_4)
"""

import json
from datetime import datetime
from pathlib import Path
from config import BASE_DIR

SAVE_SLOT_DEFS = [
    {"id": "auto", "name": "SLOT 1 [AUTO-SAVE]", "type": "auto", "filename": "save_slot_auto.json", "color": "#00f0ff"},
    {"id": "manual_1", "name": "SLOT 2 [MANUAL 1]", "type": "manual", "filename": "save_slot_manual_1.json", "color": "#00ff66"},
    {"id": "manual_2", "name": "SLOT 3 [MANUAL 2]", "type": "manual", "filename": "save_slot_manual_2.json", "color": "#ffe600"},
    {"id": "manual_3", "name": "SLOT 4 [MANUAL 3]", "type": "manual", "filename": "save_slot_manual_3.json", "color": "#ff7700"},
    {"id": "manual_4", "name": "SLOT 5 [MANUAL 4]", "type": "manual", "filename": "save_slot_manual_4.json", "color": "#b026ff"},
]


class SaveManager:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = Path(base_dir)
        self.profile_file = self.base_dir / "cyber_nova_profile.json"

        self.profile = {
            "high_score": 0,
            "max_wave": 1,
            "total_kills": 0,
            "total_scrap_collected": 0,
            "games_played": 0
        }
        self.load_profile()
        self._check_legacy_migration()

    def _check_legacy_migration(self):
        """Migrate legacy save files to new slot naming if present."""
        legacy_auto = self.base_dir / "cyber_nova_auto.json"
        target_auto = self.base_dir / "save_slot_auto.json"
        if legacy_auto.exists() and not target_auto.exists():
            try:
                target_auto.write_text(legacy_auto.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        legacy_manual = self.base_dir / "cyber_nova_manual.json"
        target_m1 = self.base_dir / "save_slot_manual_1.json"
        if legacy_manual.exists() and not target_m1.exists():
            try:
                target_m1.write_text(legacy_manual.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

    def load_profile(self):
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    self.profile.update(json.load(f))
            except Exception:
                pass

    def save_profile(self):
        try:
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=4)
        except Exception:
            pass

    def record_run(self, score: int, wave: int, kills: int, scrap: int) -> bool:
        is_new_high = score > self.profile.get("high_score", 0)
        if is_new_high:
            self.profile["high_score"] = score
        if wave > self.profile.get("max_wave", 1):
            self.profile["max_wave"] = wave

        self.profile["total_kills"] = self.profile.get("total_kills", 0) + kills
        self.profile["total_scrap_collected"] = self.profile.get("total_scrap_collected", 0) + scrap
        self.profile["games_played"] = self.profile.get("games_played", 0) + 1
        self.save_profile()
        return is_new_high

    def _get_slot_file(self, slot_id: str) -> Path:
        for s in SAVE_SLOT_DEFS:
            if s["id"] == slot_id:
                return self.base_dir / s["filename"]
        return self.base_dir / f"save_slot_{slot_id}.json"

    def save_slot(self, slot_id: str, game_state: dict) -> bool:
        """Save full game run state into specified slot."""
        filepath = self._get_slot_file(slot_id)
        try:
            data = dict(game_state)
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            data["slot_id"] = slot_id
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception:
            return False

    def load_slot(self, slot_id: str) -> dict | None:
        """Load game state from specified slot."""
        filepath = self._get_slot_file(slot_id)
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def has_slot(self, slot_id: str) -> bool:
        return self._get_slot_file(slot_id).exists()

    def get_slot_metadata(self, slot_id: str) -> dict:
        slot_def = next((s for s in SAVE_SLOT_DEFS if s["id"] == slot_id), None)
        base_meta = {
            "id": slot_id,
            "name": slot_def["name"] if slot_def else slot_id.upper(),
            "type": slot_def["type"] if slot_def else "manual",
            "color": slot_def["color"] if slot_def else "#ffffff",
            "exists": False,
            "wave": 1,
            "score": 0,
            "scrap": 0,
            "difficulty": "pilot",
            "timestamp": "EMPTY SLOT",
            "health": 100,
            "max_health": 100
        }
        data = self.load_slot(slot_id)
        if data:
            base_meta.update({
                "exists": True,
                "wave": data.get("wave", 1),
                "score": data.get("score", 0),
                "scrap": data.get("scrap", 0),
                "difficulty": data.get("difficulty", "pilot"),
                "timestamp": data.get("timestamp", "Unknown"),
                "health": data.get("player", {}).get("health", 100),
                "max_health": data.get("player", {}).get("max_health", 100)
            })
        return base_meta

    def get_all_slots_metadata(self) -> list[dict]:
        return [self.get_slot_metadata(s["id"]) for s in SAVE_SLOT_DEFS]

    def has_any_save(self) -> bool:
        return any(self.has_slot(s["id"]) for s in SAVE_SLOT_DEFS)

    def delete_slot(self, slot_id: str):
        filepath = self._get_slot_file(slot_id)
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception:
                pass


save_manager = SaveManager()
