# Buckets/config.py
from __future__ import annotations

import os
import platform
import subprocess
import warnings
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError


def config_file() -> Path:
    """Return the path to the local config.yaml file."""
    project_root = Path(__file__).resolve().parent.parent  # points to Buckets/
    return project_root / "config.yaml"


# ---------- Defaults & basic config blocks ----------


class Defaults(BaseModel):
    period: Literal["day", "week", "month", "year"] = "week"
    first_day_of_week: int = Field(ge=0, le=6, default=6)
    date_format: str = "%d/%m"
    round_decimals: int = 2
    plot_marker: Literal["braille", "fhd", "hd", "dot"] = "braille"


class DatemodeHotkeys(BaseModel):
    go_to_day: str = "g"


class HomeHotkeys(BaseModel):
    # kept
    cycle_tabs: str = "c"
    budgets: str = "b"
    new_transfer: str = "t"
    display_by_date: str = "q"
    advance_filter: str = "f"
    cycle_offset_type: str = "."
    toggle_income_mode: str = "/"
    select_prev_account: str = "["
    select_next_account: str = "]"
    toggle_use_account: str = "\\"
    datemode: DatemodeHotkeys = DatemodeHotkeys()


class RecordModalHotkeys(BaseModel):
    submit_and_template: str = "ctrl+t"


class CategoriesHotkeys(BaseModel):
    new_subcategory: str = "s"
    browse_defaults: str = "b"


class BucketsHotkeys(BaseModel):
    """New: hotkeys for bucket actions within an account."""

    new_bucket: str = "n"
    edit_bucket: str = "e"
    delete_bucket: str = "x"
    transfer_between_buckets: str = "shift+t"
    move_record_to_bucket: str = "m"


class Hotkeys(BaseModel):
    new: str = "a"
    delete: str = "d"
    edit: str = "e"
    toggle_jump_mode: str = "v"

    home: HomeHotkeys = HomeHotkeys()
    record_modal: RecordModalHotkeys = RecordModalHotkeys()
    categories: CategoriesHotkeys = CategoriesHotkeys()
    buckets: BucketsHotkeys = BucketsHotkeys()


class Symbols(BaseModel):
    line_char: str = "│"
    finish_line_char: str = "╰"
    category_color: str = "●"
    amount_positive: str = "+"
    amount_negative: str = "-"


class State(BaseModel):
    theme: str = "tokyo-night"
    check_for_updates: bool = True
    footer_visibility: bool = True


class Config(BaseModel):
    hotkeys: Hotkeys = Hotkeys()
    symbols: Symbols = Symbols()
    defaults: Defaults = Defaults()
    state: State = State()

    def __init__(self, **data: Any):
        try:
            config_data = self._load_yaml_config()
            merged_data = {**self.model_dump(), **config_data, **data}
            super().__init__(**merged_data)
            self.ensure_yaml_fields()
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field = error["loc"]
                field_path = ".".join(str(x) for x in field)
                input_value = error.get("input")
                allowed_values = None

                if error["type"] == "literal_error":
                    msg = error["msg"]
                    allowed_list = msg.split("'")[1::2]
                    allowed_values = " or ".join(f"'{v}'" for v in allowed_list)

                message = f"Invalid configuration in field '{field_path}'"
                if input_value is not None:
                    message += f"\nCurrent value: '{input_value}'"
                if allowed_values:
                    message += f"\nAllowed values: {allowed_values}"

                error_messages.append(message)

            raise ConfigurationError("\n\n".join(error_messages))

    def _load_yaml_config(self) -> dict[str, Any]:
        path = config_file()
        if not path.is_file():
            return {}
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            warnings.warn(f"Error loading config file: {e}")
            return {}

    def ensure_yaml_fields(self) -> None:
        try:
            with open(config_file(), "r") as f:
                current = yaml.safe_load(f) or {}
        except FileNotFoundError:
            current = {}

        def merge_defaults(default: dict, target: dict) -> dict:
            for k, v in default.items():
                if isinstance(v, dict):
                    target[k] = merge_defaults(v, target.get(k, {}))
                elif k not in target:
                    target[k] = v
            return target

        default_config = self.model_dump()
        merged = merge_defaults(default_config, current)

        with open(config_file(), "w") as f:
            yaml.dump(merged, f, default_flow_style=False)

    @classmethod
    def get_default(cls) -> "Config":
        return cls(
            hotkeys=Hotkeys(), symbols=Symbols(), defaults=Defaults(), state=State()
        )


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""

    pass


CONFIG: Config | None = None


def open_config_file() -> None:
    """Open the config file with the default application."""
    path = str(config_file())
    if platform.system() == "Darwin":
        subprocess.run(["open", path])
    elif platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", path])


def load_config() -> None:
    path = config_file()
    if not path.exists():
        try:
            path.touch()
            with open(path, "w") as f:
                yaml.dump(Config.get_default().model_dump(), f)
        except OSError:
            # non-fatal; we'll still try to load defaults
            pass

    global CONFIG
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            CONFIG = Config()
    except ConfigurationError as e:
        print("\nConfiguration Error:")
        print("==================")
        print(f"{e}\n")
        print("Would you like to open the config file to fix this? (y/n)")
        try:
            if input().strip().lower().startswith("y"):
                open_config_file()
                print(
                    "\nOpened config file. Please fix the error and restart the application."
                )
            else:
                print(
                    "\nPlease update your config.yaml file with valid values and try again."
                )
        except KeyboardInterrupt:
            print("\nExiting...")
        raise SystemExit(1)


def write_state(key: str, value: Any) -> None:
    """Write a nested state value to config.yaml using dot notation (e.g., 'theme' or 'foo.bar.baz')."""
    try:
        with open(config_file(), "r") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        config = {}

    keys = key.split(".")
    d = config.setdefault("state", {})
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value

    with open(config_file(), "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # update in-memory object
    global CONFIG
    if CONFIG is not None:
        d2 = CONFIG.state
        for k in keys[:-1]:
            d2 = getattr(d2, k)
        setattr(d2, keys[-1], value)
