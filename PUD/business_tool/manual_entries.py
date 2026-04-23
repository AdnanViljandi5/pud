from __future__ import annotations

import pandas as pd

from business_tool.config import APP_CONFIG
from business_tool.models import ManualBlockEntry, ManualEntryStore, ParsedWorkbook


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_manual_adjustment(value: object) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if pd.isna(numeric_value):
        return 0.0
    return numeric_value


def build_manual_entry_store(
    parsed_workbook: ParsedWorkbook | None,
    existing_store: ManualEntryStore | None = None,
) -> ManualEntryStore:
    reference_values: dict[str, str] = {}
    block_entries: dict[str, ManualBlockEntry] = {}
    future_source_values = {
        "second_file_reference": "",
        "second_file_target": "",
    }

    if parsed_workbook is not None:
        detected_reference_lookup = {
            reference_value.label: str(reference_value.value)
            for reference_value in parsed_workbook.reference_values
            if reference_value.value is not None
        }
        for reference_cell in APP_CONFIG.reference_cells:
            reference_values[reference_cell.label] = detected_reference_lookup.get(reference_cell.label, "")

    if existing_store is not None:
        for reference_label in list(reference_values.keys()):
            existing_value = existing_store.reference_values.get(reference_label, "")
            if _clean_text(existing_value):
                reference_values[reference_label] = _clean_text(existing_value)

    for block_config in APP_CONFIG.bonus_blocks:
        existing_entry = existing_store.block_entries.get(block_config.key) if existing_store is not None else None
        block_entries[block_config.key] = ManualBlockEntry(
            confirmed_target=_clean_text(existing_entry.confirmed_target) if existing_entry else "",
            manual_adjustment=_safe_manual_adjustment(existing_entry.manual_adjustment) if existing_entry else 0.0,
            extra_value=_clean_text(existing_entry.extra_value) if existing_entry else "",
            note=_clean_text(existing_entry.note) if existing_entry else "",
        )

    if existing_store is not None:
        for future_key in future_source_values:
            future_source_values[future_key] = _clean_text(existing_store.future_source_values.get(future_key, ""))

    return ManualEntryStore(
        reference_values=reference_values,
        block_entries=block_entries,
        future_source_values=future_source_values,
        general_notes=_clean_text(existing_store.general_notes) if existing_store is not None else "",
        adjustment_notes=_clean_text(existing_store.adjustment_notes) if existing_store is not None else "",
    )


def build_manual_entry_summary(manual_entry_store: ManualEntryStore) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for reference_label, reference_value in manual_entry_store.reference_values.items():
        if reference_value:
            rows.append(
                {
                    "Section": "Manual reference values",
                    "Item": reference_label,
                    "Value": reference_value,
                }
            )

    for block_key, block_entry in manual_entry_store.block_entries.items():
        if block_entry.confirmed_target:
            rows.append(
                {
                    "Section": "Manually confirmed targets",
                    "Item": block_key,
                    "Value": block_entry.confirmed_target,
                }
            )
        if block_entry.manual_adjustment:
            rows.append(
                {
                    "Section": "Manual adjustment values",
                    "Item": block_key,
                    "Value": block_entry.manual_adjustment,
                }
            )
        if block_entry.extra_value:
            rows.append(
                {
                    "Section": "Block-specific values",
                    "Item": block_key,
                    "Value": block_entry.extra_value,
                }
            )

    for item_key, item_value in manual_entry_store.future_source_values.items():
        if item_value:
            rows.append(
                {
                    "Section": "Future source values",
                    "Item": item_key,
                    "Value": item_value,
                }
            )

    if manual_entry_store.general_notes:
        rows.append(
            {
                "Section": "Notes",
                "Item": "General notes",
                "Value": manual_entry_store.general_notes,
            }
        )

    if manual_entry_store.adjustment_notes:
        rows.append(
            {
                "Section": "Notes",
                "Item": "Adjustment notes",
                "Value": manual_entry_store.adjustment_notes,
            }
        )

    return pd.DataFrame(rows)

# Confirmed business logic can connect to these stored values later, including
# workbook-derived reference values, manual target overrides, and values from a
# future second Excel source.
