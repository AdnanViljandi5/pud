from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from business_tool.config import APP_CONFIG
from business_tool.models import ParsedWorkbook, ValidationItem, ValidationResult


COMMON_REQUIRED_FIELDS = (
    "employee_number",
    "employee_name",
    "team_name",
    "position_name",
    "manager_name",
    "date_started",
    "max_bonus",
    "working_days",
    "total_bonus",
)


def build_upload_validation_result(message: str) -> ValidationResult:
    item = ValidationItem(severity="Error", section="Workbook", message=message)
    frame = pd.DataFrame([{"Severity": item.severity, "Section": item.section, "Message": item.message}])
    return ValidationResult(
        is_ready=False,
        items=[item],
        messages=[item.message],
        validation_frame=frame,
        error_count=1,
        warning_count=0,
        information_count=0,
    )


def _add_item(items: list[ValidationItem], severity: str, section: str, message: str) -> None:
    items.append(ValidationItem(severity=severity, section=section, message=message))


def _build_validation_frame(items: Iterable[ValidationItem]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Severity": item.severity,
                "Section": item.section,
                "Message": item.message,
            }
            for item in items
        ]
    )


def _display_label(normalized_block, field_name: str) -> str:
    return normalized_block.field_labels.get(field_name, field_name)


def _validate_reference_values(parsed_workbook: ParsedWorkbook, items: list[ValidationItem]) -> None:
    detected_labels = {reference_value.label for reference_value in parsed_workbook.reference_values}
    for reference_cell in APP_CONFIG.reference_cells:
        if reference_cell.label not in detected_labels:
            _add_item(
                items,
                "Warning",
                "Reference values",
                f"Please confirm the value in cell {reference_cell.cell_ref}.",
            )

    if parsed_workbook.reference_values:
        _add_item(
            items,
            "Information",
            "Reference values",
            f"{len(parsed_workbook.reference_values)} reference value(s) were found.",
        )


def _validate_block_headers(parsed_workbook: ParsedWorkbook, items: list[ValidationItem]) -> None:
    for region in parsed_workbook.regions:
        if region.missing_expected_columns:
            missing_list = ", ".join(region.missing_expected_columns)
            _add_item(
                items,
                "Error",
                region.region_name,
                f"Some expected fields were not found: {missing_list}.",
            )

        if region.duplicate_detected_columns:
            duplicate_list = ", ".join(region.duplicate_detected_columns)
            _add_item(
                items,
                "Warning",
                region.region_name,
                f"Some column names appear more than once: {duplicate_list}.",
            )

        if region.ambiguous_columns:
            ambiguous_list = ", ".join(region.ambiguous_columns)
            _add_item(
                items,
                "Warning",
                region.region_name,
                f"Some columns may need confirmation because their names repeat: {ambiguous_list}.",
            )

        if region.region_name == "Bonus block 4" and region.ambiguous_columns:
            _add_item(
                items,
                "Warning",
                region.region_name,
                "Block 4 includes repeated column names. Please confirm which columns should be used.",
            )


def _validate_block_rows(parsed_workbook: ParsedWorkbook, items: list[ValidationItem]) -> None:
    block_config_lookup = {block.name: block for block in APP_CONFIG.bonus_blocks}
    for region in parsed_workbook.regions:
        row_count = len(region.frame.index)
        config = block_config_lookup.get(region.region_name)

        if row_count == 0:
            _add_item(
                items,
                "Error",
                region.region_name,
                "No data rows were found in this section.",
            )
            continue

        if row_count == 1:
            _add_item(
                items,
                "Information",
                region.region_name,
                "Only 1 row was found in this section. Please confirm that this is correct.",
            )

        if config is not None and config.data_end_row is None and row_count >= config.max_data_rows:
            _add_item(
                items,
                "Warning",
                region.region_name,
                "The row count is close to the expected limit. Please confirm that all rows were included.",
            )


def _validate_dates(parsed_workbook: ParsedWorkbook, items: list[ValidationItem]) -> None:
    for normalized_block in parsed_workbook.normalized_blocks:
        frame = normalized_block.normalized_frame
        if "date_started" not in frame.columns or frame.empty:
            continue

        non_blank_dates = frame["date_started"].dropna()
        if non_blank_dates.empty:
            continue

        parsed_dates = pd.to_datetime(non_blank_dates, errors="coerce")
        invalid_count = int(parsed_dates.isna().sum())
        if invalid_count > 0:
            _add_item(
                items,
                "Warning",
                normalized_block.block_name,
                f"Some Date started values could not be read clearly ({invalid_count} row(s)).",
            )


def _validate_important_fields(parsed_workbook: ParsedWorkbook, items: list[ValidationItem]) -> None:
    for normalized_block in parsed_workbook.normalized_blocks:
        frame = normalized_block.normalized_frame

        if frame.empty:
            continue

        for field_name in COMMON_REQUIRED_FIELDS:
            if field_name not in frame.columns:
                _add_item(
                    items,
                    "Error",
                    normalized_block.block_name,
                    f"This field is not available: {_display_label(normalized_block, field_name)}.",
                )
                continue

            blank_mask = frame[field_name].isna() | (frame[field_name].astype("string").str.strip() == "")
            blank_count = int(blank_mask.sum())
            if blank_count > 0:
                _add_item(
                    items,
                    "Warning",
                    normalized_block.block_name,
                    f"Please confirm {_display_label(normalized_block, field_name)} for {blank_count} row(s).",
                )


def validate_parsed_workbook(parsed_workbook: ParsedWorkbook) -> ValidationResult:
    items: list[ValidationItem] = []

    _validate_reference_values(parsed_workbook, items)
    _validate_block_headers(parsed_workbook, items)
    _validate_block_rows(parsed_workbook, items)
    _validate_dates(parsed_workbook, items)
    _validate_important_fields(parsed_workbook, items)

    for issue in parsed_workbook.issues:
        _add_item(items, "Warning", "Workbook", issue)

    if not items:
        _add_item(items, "Information", "Workbook", "Review completed. The workbook is ready for the next step.")

    validation_frame = _build_validation_frame(items)
    error_count = sum(1 for item in items if item.severity == "Error")
    warning_count = sum(1 for item in items if item.severity == "Warning")
    information_count = sum(1 for item in items if item.severity == "Information")
    messages = [item.message for item in items]

    return ValidationResult(
        is_ready=error_count == 0,
        items=items,
        messages=messages,
        validation_frame=validation_frame,
        error_count=error_count,
        warning_count=warning_count,
        information_count=information_count,
    )

# Structural checks can be extended here later if the final workbook layout
# introduces more fixed sections or clarifies additional field meanings.
