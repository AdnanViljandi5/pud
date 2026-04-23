from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from business_tool.models import (
    BlockCalculationResult,
    CalculationResult,
    CalculationSummary,
    CalculationWarning,
    ManualBlockEntry,
    ManualEntryStore,
    NormalizedBlock,
    ParsedWorkbook,
    ReferenceValue,
    ValidationResult,
)


BLOCK_1_COMPONENT_FIELDS = (
    "personal_component_30",
    "spr_component_35",
    "sporh_component_35",
)

BLOCK_2_COMPONENT_FIELDS = (
    "personal_component_50",
    "spr_component_25",
    "sporh_component_25",
)

BLOCK_3_COMPONENT_FIELDS = (
    "sl_checkpoint_compliance_50",
    "google_review_or_personal_for_kaur_50",
    "insurance_extra_sale_bonus",
)

BLOCK_4_DRAFT_FIELDS = {
    "act_bonus_left": "max_bonus_actual_working_days_2",
    "act_bonus_right": "sales_leads_component_max_33_3",
}


def _reference_lookup(reference_values: Iterable[ReferenceValue], manual_entry_store: ManualEntryStore) -> dict[str, object]:
    lookup = {reference_value.label: reference_value.value for reference_value in reference_values}
    for reference_label, manual_value in manual_entry_store.reference_values.items():
        if manual_value:
            lookup[reference_label] = manual_value
    return lookup


def _coerce_scalar_number(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_series(frame: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in frame.columns:
        return pd.Series([pd.NA] * len(frame.index), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column_name], errors="coerce")


def _prepare_base_output(normalized_block: NormalizedBlock, manual_entry: ManualBlockEntry) -> pd.DataFrame:
    output_frame = normalized_block.normalized_frame.copy()
    output_frame["manual_confirmed_target"] = manual_entry.confirmed_target or pd.NA
    output_frame["manual_adjustment"] = manual_entry.manual_adjustment
    output_frame["manual_extra_value"] = manual_entry.extra_value or pd.NA
    output_frame["manual_note"] = manual_entry.note or pd.NA
    output_frame["calculation_status"] = "Review needed"
    output_frame["calculation_note"] = "Additional confirmation is required before final output."
    output_frame["calculated_bonus_amount"] = pd.NA
    return output_frame


def _safe_numeric_mask(frame: pd.DataFrame, field_names: tuple[str, ...]) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for field_name in field_names:
        if field_name not in frame.columns:
            return pd.Series(False, index=frame.index)
        mask &= pd.to_numeric(frame[field_name], errors="coerce").notna()
    return mask


def _apply_weighted_component_pattern(
    output_frame: pd.DataFrame,
    component_fields: tuple[str, ...],
    reference_value: float | None,
    manual_adjustment: float,
) -> tuple[pd.DataFrame, pd.Series]:
    component_series = [_coerce_series(output_frame, field_name) for field_name in component_fields]
    working_days = _coerce_series(output_frame, "working_days")
    component_total = sum(component_series)

    output_frame["draft_component_total"] = component_total
    output_frame["draft_working_days_adjusted_value"] = pd.NA

    if reference_value is None or reference_value == 0:
        return output_frame, pd.Series(False, index=output_frame.index)

    complete_mask = _safe_numeric_mask(output_frame, component_fields + ("working_days",))
    output_frame.loc[complete_mask, "draft_working_days_adjusted_value"] = (
        component_total.loc[complete_mask] / reference_value
    ) * working_days.loc[complete_mask]
    output_frame.loc[complete_mask, "calculated_bonus_amount"] = (
        output_frame.loc[complete_mask, "draft_working_days_adjusted_value"] + manual_adjustment
    )
    return output_frame, complete_mask


def _set_partial_row_messages(
    output_frame: pd.DataFrame,
    complete_mask: pd.Series,
    available_status: str,
    available_note: str,
    missing_note: str,
) -> None:
    output_frame.loc[complete_mask, "calculation_status"] = available_status
    output_frame.loc[complete_mask, "calculation_note"] = available_note
    output_frame.loc[~complete_mask, "calculation_status"] = "Additional confirmation required"
    output_frame.loc[~complete_mask, "calculation_note"] = missing_note


def calculate_block_1(
    block_data: NormalizedBlock,
    top_reference_values: dict[str, object],
    manual_inputs: ManualEntryStore,
) -> BlockCalculationResult:
    manual_entry = manual_inputs.block_entries.get(block_data.block_key, ManualBlockEntry())
    output_frame = _prepare_base_output(block_data, manual_entry)
    warnings: list[str] = []

    reference_e4 = _coerce_scalar_number(top_reference_values.get("E4"))
    if reference_e4 is None or reference_e4 == 0:
        warnings.append("Block 1 needs a confirmed E4 reference value before a result can be prepared.")
        output_frame["draft_component_total"] = sum(_coerce_series(output_frame, field_name) for field_name in BLOCK_1_COMPONENT_FIELDS)
        output_frame["draft_working_days_adjusted_value"] = pd.NA
        output_frame["calculation_note"] = "Please confirm the E4 reference value."
    else:
        # Draft reference only:
        # Example provided: =((I10+J10+H10)/$E$4)*K10
        # This section should be revisited once the final workbook logic is confirmed.
        output_frame, complete_mask = _apply_weighted_component_pattern(
            output_frame,
            BLOCK_1_COMPONENT_FIELDS,
            reference_e4,
            manual_entry.manual_adjustment,
        )
        output_frame["draft_block_1_example_value"] = output_frame["draft_working_days_adjusted_value"]
        _set_partial_row_messages(
            output_frame,
            complete_mask,
            "Result available for review",
            "A draft result has been prepared for Block 1.",
            "Additional input or confirmation is needed before Block 1 can be finalized.",
        )
        warnings.append("Block 1 includes a draft result and should be reviewed before final use.")

    if manual_entry.confirmed_target:
        warnings.append("Block 1 includes a manually entered target value.")

    return BlockCalculationResult(
        block_key=block_data.block_key,
        block_name=block_data.block_name,
        output_frame=output_frame,
        warning_messages=warnings,
        rows_prepared=len(output_frame.index),
        status=(
            "Result available for review"
            if output_frame["calculated_bonus_amount"].notna().any()
            else "Additional confirmation required"
        ) if len(output_frame.index) > 0 else "No data loaded",
    )


def calculate_block_2(
    block_data: NormalizedBlock,
    top_reference_values: dict[str, object],
    manual_inputs: ManualEntryStore,
) -> BlockCalculationResult:
    manual_entry = manual_inputs.block_entries.get(block_data.block_key, ManualBlockEntry())
    output_frame = _prepare_base_output(block_data, manual_entry)
    warnings: list[str] = []
    reference_e4 = _coerce_scalar_number(top_reference_values.get("E4"))

    if reference_e4 is None or reference_e4 == 0:
        warnings.append("Block 2 needs a confirmed E4 reference value before a result can be prepared.")
        output_frame["draft_component_total"] = sum(_coerce_series(output_frame, field_name) for field_name in BLOCK_2_COMPONENT_FIELDS)
        output_frame["draft_working_days_adjusted_value"] = pd.NA
        output_frame["calculation_note"] = "Please confirm the E4 reference value."
    else:
        output_frame, complete_mask = _apply_weighted_component_pattern(
            output_frame,
            BLOCK_2_COMPONENT_FIELDS,
            reference_e4,
            manual_entry.manual_adjustment,
        )
        output_frame["draft_block_2_example_value"] = output_frame["draft_working_days_adjusted_value"]
        _set_partial_row_messages(
            output_frame,
            complete_mask,
            "Result available for review",
            "A draft result has been prepared for Block 2.",
            "Additional input or confirmation is needed before Block 2 can be finalized.",
        )
        warnings.append("Block 2 includes a draft result and should be reviewed before final use.")

    if manual_entry.confirmed_target:
        warnings.append("Block 2 includes a manually entered target value.")

    return BlockCalculationResult(
        block_key=block_data.block_key,
        block_name=block_data.block_name,
        output_frame=output_frame,
        warning_messages=warnings,
        rows_prepared=len(output_frame.index),
        status=(
            "Result available for review"
            if output_frame["calculated_bonus_amount"].notna().any()
            else "Additional confirmation required"
        ) if len(output_frame.index) > 0 else "No data loaded",
    )


def calculate_block_3(
    block_data: NormalizedBlock,
    top_reference_values: dict[str, object],
    manual_inputs: ManualEntryStore,
) -> BlockCalculationResult:
    manual_entry = manual_inputs.block_entries.get(block_data.block_key, ManualBlockEntry())
    output_frame = _prepare_base_output(block_data, manual_entry)
    warnings = [
        "Block 3 needs additional confirmation before a final result can be prepared.",
    ]

    component_total = sum(_coerce_series(output_frame, field_name) for field_name in BLOCK_3_COMPONENT_FIELDS)
    output_frame["draft_block_3_component_total"] = component_total
    output_frame["draft_block_3_review_value"] = component_total + manual_entry.manual_adjustment
    output_frame["calculated_bonus_amount"] = pd.NA
    output_frame["calculation_status"] = "Additional confirmation required"
    output_frame["calculation_note"] = (
        "Insurance extra sale bonus is included in the review value. "
        "Please confirm the final treatment for Block 3."
    )

    if manual_entry.extra_value:
        warnings.append("Block 3 includes an additional entered value.")

    return BlockCalculationResult(
        block_key=block_data.block_key,
        block_name=block_data.block_name,
        output_frame=output_frame,
        warning_messages=warnings,
        rows_prepared=len(output_frame.index),
        status="Additional confirmation required" if len(output_frame.index) > 0 else "No data loaded",
    )


def calculate_block_4(
    block_data: NormalizedBlock,
    top_reference_values: dict[str, object],
    manual_inputs: ManualEntryStore,
) -> BlockCalculationResult:
    manual_entry = manual_inputs.block_entries.get(block_data.block_key, ManualBlockEntry())
    output_frame = _prepare_base_output(block_data, manual_entry)
    warnings: list[str] = [
        "Block 4 contains repeated columns and should be reviewed carefully.",
    ]

    left_field = BLOCK_4_DRAFT_FIELDS["act_bonus_left"]
    right_field = BLOCK_4_DRAFT_FIELDS["act_bonus_right"]
    left_component = _coerce_series(output_frame, left_field)
    right_component = _coerce_series(output_frame, right_field)
    complete_mask = _safe_numeric_mask(output_frame, (left_field, right_field))

    # Draft reference only:
    # Example provided: Act bonus = J29 + L29
    # The exact field meanings for these repeated and similar columns still need confirmation.
    # These field mappings are intentionally isolated here so they can be updated
    # quickly after the actual workbook is checked.
    output_frame["draft_block_4_act_bonus_example"] = left_component + right_component
    output_frame.loc[complete_mask, "calculated_bonus_amount"] = (
        output_frame.loc[complete_mask, "draft_block_4_act_bonus_example"] + manual_entry.manual_adjustment
    )
    _set_partial_row_messages(
        output_frame,
        complete_mask,
        "Result available for review",
        "A draft result has been prepared for Block 4.",
        "Additional input or confirmation is needed before Block 4 can be finalized.",
    )
    warnings.append("Block 4 includes a draft result and should be reviewed before final use.")

    return BlockCalculationResult(
        block_key=block_data.block_key,
        block_name=block_data.block_name,
        output_frame=output_frame,
        warning_messages=warnings,
        rows_prepared=len(output_frame.index),
        status=(
            "Result available for review"
            if output_frame["calculated_bonus_amount"].notna().any()
            else "Additional confirmation required"
        ) if len(output_frame.index) > 0 else "No data loaded",
    )


def _empty_calculation_result() -> CalculationResult:
    output_frame = pd.DataFrame(columns=["Status", "Notes"])
    return CalculationResult(
        block_results=[],
        warnings=[],
        block_summary_frame=pd.DataFrame(),
        summary=CalculationSummary(
            rows_prepared=0,
            ready_rows=0,
            output_status="No data loaded",
            warning_count=0,
        ),
        output_frame=output_frame,
    )


def run_calculation_engine(
    parsed_blocks: list[NormalizedBlock],
    top_reference_values: list[ReferenceValue],
    manual_inputs: ManualEntryStore,
    validation_result: ValidationResult,
) -> CalculationResult:
    if not parsed_blocks:
        return _empty_calculation_result()

    reference_lookup = _reference_lookup(top_reference_values, manual_inputs)
    block_result_map: dict[str, BlockCalculationResult] = {}

    for block_data in parsed_blocks:
        if block_data.block_key == "bonus_block_1":
            block_result = calculate_block_1(block_data, reference_lookup, manual_inputs)
        elif block_data.block_key == "bonus_block_2":
            block_result = calculate_block_2(block_data, reference_lookup, manual_inputs)
        elif block_data.block_key == "bonus_block_3":
            block_result = calculate_block_3(block_data, reference_lookup, manual_inputs)
        elif block_data.block_key == "bonus_block_4":
            block_result = calculate_block_4(block_data, reference_lookup, manual_inputs)
        else:
            output_frame = _prepare_base_output(block_data, manual_inputs.block_entries.get(block_data.block_key, ManualBlockEntry()))
            block_result = BlockCalculationResult(
                block_key=block_data.block_key,
                block_name=block_data.block_name,
                output_frame=output_frame,
                warning_messages=["This section is available for review, but no calculation has been set up yet."],
                rows_prepared=len(output_frame.index),
                status="Additional confirmation required",
            )
        block_result_map[block_data.block_key] = block_result

    ordered_block_results = [block_result_map[block_data.block_key] for block_data in parsed_blocks]
    combined_output_frame = pd.concat(
        [block_result.output_frame for block_result in ordered_block_results],
        ignore_index=True,
        sort=False,
    ) if ordered_block_results else pd.DataFrame()

    warning_items: list[CalculationWarning] = []
    for block_result in ordered_block_results:
        for message in block_result.warning_messages:
            warning_items.append(CalculationWarning(block_name=block_result.block_name, message=message))

    block_summary_frame = pd.DataFrame(
        [
            {
                "Block": block_result.block_name,
                "Rows prepared": block_result.rows_prepared,
                "Status": block_result.status,
                "Warnings": len(block_result.warning_messages),
            }
            for block_result in ordered_block_results
        ]
    )

    output_status = "Results available for review"
    if validation_result.error_count > 0:
        output_status = "Action required"
    elif not combined_output_frame.empty and combined_output_frame["calculated_bonus_amount"].notna().sum() == 0:
        output_status = "Additional confirmation required"

    return CalculationResult(
        block_results=ordered_block_results,
        warnings=warning_items,
        block_summary_frame=block_summary_frame,
        summary=CalculationSummary(
            rows_prepared=len(combined_output_frame.index),
            ready_rows=int(combined_output_frame["calculated_bonus_amount"].notna().sum()),
            output_status=output_status,
            warning_count=len(warning_items),
        ),
        output_frame=combined_output_frame,
    )


def run_calculation(
    parsed_workbook: ParsedWorkbook,
    validation_result: ValidationResult,
    manual_entry_store: ManualEntryStore,
) -> CalculationResult:
    return run_calculation_engine(
        parsed_workbook.normalized_blocks,
        parsed_workbook.reference_values,
        manual_entry_store,
        validation_result,
    )
