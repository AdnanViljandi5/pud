from __future__ import annotations

from io import BytesIO

import pandas as pd

from business_tool.config import APP_CONFIG
from business_tool.models import CalculationResult, ExportPackage


RESULT_EXPORT_COLUMNS = [
    "employee_name",
    "position_name",
    "max_bonus",
    "working_days",
    "draft_component_total",
    "draft_working_days_adjusted_value",
    "draft_block_1_example_value",
    "draft_block_2_example_value",
    "draft_block_3_component_total",
    "draft_block_3_review_value",
    "draft_block_4_act_bonus_example",
    "calculated_bonus_amount",
    "manual_confirmed_target",
    "manual_adjustment",
    "calculation_status",
    "calculation_note",
    "manual_note",
]


def _has_exportable_rows(frame: pd.DataFrame) -> bool:
    if frame.empty:
        return False

    if "calculated_bonus_amount" in frame.columns and frame["calculated_bonus_amount"].notna().any():
        return True

    if "calculation_status" in frame.columns:
        status_values = frame["calculation_status"].fillna("").astype("string").str.strip()
        return (status_values == "Result available for review").any()

    return False


def calculation_result_is_exportable(calculation_result: CalculationResult | None) -> bool:
    if calculation_result is None:
        return False

    if _has_exportable_rows(calculation_result.output_frame):
        return True

    return any(_has_exportable_rows(block_result.output_frame) for block_result in calculation_result.block_results)


def _build_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    export_frame = pd.DataFrame(index=frame.index)
    column_labels = {
        "employee_name": "Name",
        "position_name": "Position",
        "max_bonus": "Max bonus",
        "working_days": "Working days",
        "draft_component_total": "Calculated values",
        "draft_working_days_adjusted_value": "Working-days adjusted value",
        "draft_block_1_example_value": "Block 1 draft value",
        "draft_block_2_example_value": "Block 2 draft value",
        "draft_block_3_component_total": "Block 3 component total",
        "draft_block_3_review_value": "Block 3 review value",
        "draft_block_4_act_bonus_example": "Block 4 draft Act bonus",
        "calculated_bonus_amount": "Final output",
        "manual_confirmed_target": "Confirmed target",
        "manual_adjustment": "Manual adjustment",
        "calculation_status": "Status",
        "calculation_note": "Required confirmation",
        "manual_note": "Notes",
    }

    for column_name in RESULT_EXPORT_COLUMNS:
        if column_name in frame.columns:
            export_frame[column_labels[column_name]] = frame[column_name]

    return export_frame


def _filter_final_export_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    filtered_frame = frame.copy()

    if "calculated_bonus_amount" in filtered_frame.columns:
        final_mask = filtered_frame["calculated_bonus_amount"].notna()
        if final_mask.any():
            return filtered_frame.loc[final_mask].copy()

    if "calculation_status" in filtered_frame.columns:
        status_values = filtered_frame["calculation_status"].fillna("").astype("string").str.strip()
        review_mask = status_values == "Result available for review"
        if review_mask.any():
            return filtered_frame.loc[review_mask].copy()

    return filtered_frame.iloc[0:0].copy()


def build_export_package(calculation_result: CalculationResult) -> ExportPackage:
    if not calculation_result_is_exportable(calculation_result):
        raise ValueError("No result rows are available for export.")

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if not calculation_result.block_summary_frame.empty:
            calculation_result.block_summary_frame.to_excel(writer, index=False, sheet_name="Summary")

        if calculation_result.warnings:
            warning_frame = pd.DataFrame(
                [
                    {
                        "Block": warning.block_name,
                        "Message": warning.message,
                    }
                    for warning in calculation_result.warnings
                ]
            )
            warning_frame.to_excel(writer, index=False, sheet_name="Review Notes")

        for index, block_result in enumerate(calculation_result.block_results, start=1):
            sheet_name = f"Block {index}"
            final_block_frame = _filter_final_export_rows(block_result.output_frame)
            if final_block_frame.empty:
                continue

            export_frame = _build_export_frame(final_block_frame)
            if not export_frame.empty:
                export_frame.to_excel(writer, index=False, sheet_name=sheet_name)

        combined_export_frame = _build_export_frame(_filter_final_export_rows(calculation_result.output_frame))
        combined_export_frame.to_excel(writer, index=False, sheet_name="All Results")

    return ExportPackage(
        file_name=APP_CONFIG.output_file_name,
        content=buffer.getvalue(),
    )

# Future export sheets can be added here for audit details, manual overrides,
# and business sign-off columns once the final workbook output is defined.
