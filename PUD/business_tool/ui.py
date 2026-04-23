from __future__ import annotations

import pandas as pd
import streamlit as st

from business_tool.calculation import run_calculation
from business_tool.config import APP_CONFIG
from business_tool.export_output import build_export_package, calculation_result_is_exportable
from business_tool.manual_entries import build_manual_entry_store, build_manual_entry_summary
from business_tool.settings_config import APP_SETTINGS
from business_tool.models import CalculationResult, ManualBlockEntry, ManualEntryStore, ParsedWorkbook, ValidationResult, WorkbookSource, WorkbookSourceCollection
from business_tool.parsing import load_sheet_preview
from business_tool.source_manager import build_source_collection, load_primary_workbook, parse_primary_workbook
from business_tool.validation import build_upload_validation_result, validate_parsed_workbook


st.set_page_config(
    page_title=APP_CONFIG.page_title,
    layout="wide",
)


def _initialize_state() -> None:
    defaults = {
        "upload_signature": None,
        "workbook_sources": WorkbookSourceCollection(),
        "workbook_error": None,
        "selected_sheet_name": None,
        "parsed_workbook": None,
        "validation_result": None,
        "manual_entry_store": build_manual_entry_store(None),
        "calculation_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_workbook_state() -> None:
    st.session_state["upload_signature"] = None
    st.session_state["workbook_sources"] = WorkbookSourceCollection()
    st.session_state["workbook_error"] = None
    st.session_state["selected_sheet_name"] = None
    st.session_state["parsed_workbook"] = None
    st.session_state["validation_result"] = None
    st.session_state["manual_entry_store"] = build_manual_entry_store(None)
    st.session_state["calculation_result"] = None


def _safe_manual_adjustment(value: object) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if pd.isna(numeric_value):
        return 0.0
    return numeric_value


def _render_header() -> None:
    st.title(APP_CONFIG.page_title)
    st.caption("Upload the workbook, review the information, complete any required values, and prepare the results.")


def _render_overview(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    metrics = st.columns(4)

    file_status = "No file selected"
    rows_loaded = 0
    review_status = "Awaiting file"
    result_status = "Not available"

    if parsed_workbook is not None:
        file_status = "Loaded"
        rows_loaded = parsed_workbook.summary.row_count
        review_status = "Ready"

    if validation_result is not None:
        if validation_result.error_count > 0:
            review_status = "Action required"
        elif validation_result.warning_count > 0:
            review_status = "Review needed"

    if st.session_state["calculation_result"] is not None:
        result_status = "Available"

    metrics[0].metric("File status", file_status)
    metrics[1].metric("Rows loaded", rows_loaded)
    metrics[2].metric("Data check", review_status)
    metrics[3].metric("Results", result_status)


def _render_upload_section() -> None:
    st.subheader("Upload File")
    uploaded_file = st.file_uploader(
        APP_CONFIG.upload_label,
        type=["xlsx", "xlsm", "xltx", "xltm"],
    )

    if uploaded_file is None:
        if st.session_state["upload_signature"] is not None:
            _reset_workbook_state()
        return

    upload_signature = f"{uploaded_file.name}:{uploaded_file.size}"
    if upload_signature != st.session_state["upload_signature"]:
        try:
            workbook_source = load_primary_workbook(uploaded_file)
            parsed_workbook = parse_primary_workbook(workbook_source)
            validation_result = validate_parsed_workbook(parsed_workbook)
        except ValueError as exc:
            st.session_state["upload_signature"] = upload_signature
            st.session_state["workbook_sources"] = WorkbookSourceCollection()
            st.session_state["workbook_error"] = str(exc)
            st.session_state["selected_sheet_name"] = None
            st.session_state["parsed_workbook"] = None
            st.session_state["validation_result"] = build_upload_validation_result(str(exc))
            st.session_state["manual_entry_store"] = build_manual_entry_store(None)
            st.session_state["calculation_result"] = None
        else:
            selected_sheet_name = workbook_source.sheet_names[0]
            existing_manual_store = st.session_state.get("manual_entry_store")
            st.session_state["upload_signature"] = upload_signature
            st.session_state["workbook_sources"] = build_source_collection(workbook_source)
            st.session_state["workbook_error"] = None
            st.session_state["selected_sheet_name"] = selected_sheet_name
            st.session_state["parsed_workbook"] = parsed_workbook
            st.session_state["validation_result"] = validation_result
            st.session_state["manual_entry_store"] = build_manual_entry_store(parsed_workbook, existing_manual_store)
            st.session_state["calculation_result"] = None

    st.caption(f"Selected file: {uploaded_file.name}")
    if st.session_state["workbook_error"]:
        st.error(st.session_state["workbook_error"])
        return

    workbook_sources: WorkbookSourceCollection = st.session_state["workbook_sources"]
    workbook_source: WorkbookSource | None = workbook_sources.primary_source
    if workbook_source is None:
        return

    st.write("Available worksheets")
    st.write(", ".join(workbook_source.sheet_names))

    current_sheet = st.session_state["selected_sheet_name"] or workbook_source.sheet_names[0]
    if current_sheet not in workbook_source.sheet_names:
        current_sheet = workbook_source.sheet_names[0]

    selected_sheet = st.selectbox(
        "Select worksheet",
        workbook_source.sheet_names,
        index=workbook_source.sheet_names.index(current_sheet),
        key="selected_sheet_name",
    )

    try:
        preview_frame = load_sheet_preview(workbook_source, selected_sheet)
    except ValueError as exc:
        st.error(str(exc))
        return

    st.write("Worksheet preview")
    if preview_frame.empty:
        st.info("No preview rows are available for the selected worksheet.")
        return

    st.dataframe(preview_frame, use_container_width=True, hide_index=True)


def _render_review_section(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    if parsed_workbook is None or validation_result is None:
        st.info("Upload a file to review the data.")
        return

    metrics = st.columns(3)
    metrics[0].metric("Sheets scanned", parsed_workbook.summary.sheet_count)
    metrics[1].metric("Sections loaded", parsed_workbook.summary.region_count)
    metrics[2].metric("Rows loaded", parsed_workbook.summary.row_count)

    if parsed_workbook.reference_values:
        st.write("Reference values")
        reference_frame = pd.DataFrame(
            [
                {
                    "Reference": reference_value.label,
                    "Cell": reference_value.cell_ref,
                    "Value": reference_value.value,
                }
                for reference_value in parsed_workbook.reference_values
            ]
        )
        st.dataframe(reference_frame, use_container_width=True, hide_index=True)

    block_labels = {
        "bonus_block_1": "Block 1",
        "bonus_block_2": "Block 2",
        "bonus_block_3": "Block 3",
        "bonus_block_4": "Block 4",
    }

    normalized_lookup = {
        normalized_block.block_key: normalized_block
        for normalized_block in parsed_workbook.normalized_blocks
    }

    for index, block_config in enumerate(APP_CONFIG.bonus_blocks):
        display_name = block_labels.get(block_config.key, f"Block {index + 1}")
        st.write(display_name)

        raw_region = next(
            (region for region in parsed_workbook.regions if region.region_name == block_config.name),
            None,
        )
        normalized_block = normalized_lookup.get(block_config.key)

        row_count = len(raw_region.frame.index) if raw_region is not None else 0
        found_columns = 0
        if raw_region is not None:
            found_columns = len(block_config.expected_columns) - len(raw_region.missing_expected_columns)

        summary_columns = st.columns(3)
        summary_columns[0].metric("Rows", row_count)
        summary_columns[1].metric("Fields found", found_columns)
        summary_columns[2].metric("Expected fields", len(block_config.expected_columns))

        if found_columns == len(block_config.expected_columns):
            st.caption("Required fields are available.")
        else:
            st.caption("Some fields may need review.")

        if raw_region is None or raw_region.frame.empty:
            st.info("No rows were found for this section.")
            continue

        preview_columns = ["Source Row"]
        if normalized_block is not None:
            preview_columns.extend(
                field_name for field_name in normalized_block.shared_fields if field_name in normalized_block.normalized_frame.columns
            )
        preview_frame = raw_region.frame.copy()
        if normalized_block is not None:
            normalized_preview = normalized_block.normalized_frame.copy()
            user_friendly_preview = pd.DataFrame(index=normalized_preview.index)
            for field_name in preview_columns:
                if field_name == "Source Row":
                    user_friendly_preview["Source Row"] = raw_region.frame["Source Row"]
                    continue
                display_label = normalized_block.field_labels.get(field_name, field_name)
                user_friendly_preview[display_label] = normalized_preview[field_name]
            st.dataframe(user_friendly_preview, use_container_width=True, hide_index=True)
        else:
            st.dataframe(preview_frame.head(10), use_container_width=True, hide_index=True)

    if not validation_result.validation_frame.empty:
        status_columns = st.columns(3)
        status_columns[0].metric("Errors", validation_result.error_count)
        status_columns[1].metric("Warnings", validation_result.warning_count)
        status_columns[2].metric("Notices", validation_result.information_count)


def _render_validation_section(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    if validation_result is None:
        st.info("Upload a file before entering required values.")
        return

    manual_entry_store: ManualEntryStore = st.session_state["manual_entry_store"]

    if parsed_workbook is None:
        st.info("Upload a file before entering missing values.")
        return

    st.write("Some values need to be confirmed before the calculation can be completed.")
    if validation_result.error_count == 0 and validation_result.warning_count == 0:
        st.info("You can still enter reference values, notes, and adjustments if needed.")

    block_labels = {
        "bonus_block_1": "Block 1",
        "bonus_block_2": "Block 2",
        "bonus_block_3": "Block 3",
        "bonus_block_4": "Block 4",
    }

    with st.form("manual_values_form"):
        st.write("Reference values")
        reference_columns = st.columns(3)
        updated_reference_values: dict[str, str] = {}
        for index, reference_cell in enumerate(APP_CONFIG.reference_cells):
            column = reference_columns[index % 3]
            current_value = manual_entry_store.reference_values.get(reference_cell.label, "")
            with column:
                updated_reference_values[reference_cell.label] = st.text_input(
                    f"Reference value {reference_cell.label}",
                    value=current_value,
                )

        st.write("Values by section")
        updated_block_entries: dict[str, ManualBlockEntry] = {}
        for block_config in APP_CONFIG.bonus_blocks:
            block_label = block_labels.get(block_config.key, block_config.name)
            existing_entry = manual_entry_store.block_entries.get(block_config.key, ManualBlockEntry())
            with st.expander(block_label, expanded=False):
                confirmed_target = st.text_input(
                    f"{block_label} target value",
                    value=existing_entry.confirmed_target,
                    key=f"{block_config.key}_confirmed_target",
                )
                manual_adjustment = st.number_input(
                    f"{block_label} adjustment value",
                    value=_safe_manual_adjustment(existing_entry.manual_adjustment),
                    step=0.01,
                    key=f"{block_config.key}_manual_adjustment",
                )
                extra_value = st.text_input(
                    f"{block_label} additional value",
                    value=existing_entry.extra_value,
                    key=f"{block_config.key}_extra_value",
                )
                note = st.text_area(
                    f"{block_label} note",
                    value=existing_entry.note,
                    key=f"{block_config.key}_note",
                )
                updated_block_entries[block_config.key] = ManualBlockEntry(
                    confirmed_target=confirmed_target.strip(),
                    manual_adjustment=manual_adjustment,
                    extra_value=extra_value.strip(),
                    note=note.strip(),
                )

        st.write("Additional values")
        future_second_file_reference = st.text_input(
            "Additional reference value",
            value=manual_entry_store.future_source_values.get("second_file_reference", ""),
        )
        future_second_file_target = st.text_input(
            "Additional target value",
            value=manual_entry_store.future_source_values.get("second_file_target", ""),
        )
        general_notes = st.text_area(
            "General notes",
            value=manual_entry_store.general_notes,
        )
        adjustment_notes = st.text_area(
            "Adjustment notes",
            value=manual_entry_store.adjustment_notes,
        )

        submitted = st.form_submit_button("Save Entries")

    if submitted:
        st.session_state["manual_entry_store"] = ManualEntryStore(
            reference_values={key: value.strip() for key, value in updated_reference_values.items()},
            block_entries=updated_block_entries,
            future_source_values={
                "second_file_reference": future_second_file_reference.strip(),
                "second_file_target": future_second_file_target.strip(),
            },
            general_notes=general_notes.strip(),
            adjustment_notes=adjustment_notes.strip(),
        )
        st.success("Entries saved.")

    summary_frame = build_manual_entry_summary(st.session_state["manual_entry_store"])
    if summary_frame.empty:
        st.info("No additional values have been entered yet.")
    else:
        st.write("Saved entries")
        st.dataframe(summary_frame, use_container_width=True, hide_index=True)

    # Confirmed business logic can connect here later to apply manual values to
    # calculation steps, exports, and any second-file reconciliation process.


def _render_check_section(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    if validation_result is None:
        st.info("Upload a file before checking the data.")
        return

    left_col, right_col = st.columns([3, 2])
    with left_col:
        st.write("Review status")
        if validation_result.error_count > 0:
            error_messages = [item.message for item in validation_result.items if item.severity == "Error"]
            st.error("\n".join(error_messages))
        if validation_result.warning_count > 0:
            warning_messages = [item.message for item in validation_result.items if item.severity == "Warning"]
            st.warning("\n".join(warning_messages))
        information_messages = [item.message for item in validation_result.items if item.severity == "Information"]
        if information_messages:
            st.info("\n".join(information_messages))

    with right_col:
        st.write("File summary")
        if parsed_workbook is None:
            st.write("Sheets scanned: 0")
            st.write("Sections loaded: 0")
            st.write("Rows loaded: 0")
        else:
            st.write(f"Sheets scanned: {parsed_workbook.summary.sheet_count}")
            st.write(f"Sections loaded: {parsed_workbook.summary.region_count}")
            st.write(f"Rows loaded: {parsed_workbook.summary.row_count}")
        st.write(f"Errors: {validation_result.error_count}")
        st.write(f"Warnings: {validation_result.warning_count}")
        st.write(f"Notices: {validation_result.information_count}")

    if validation_result.error_count == 0 and validation_result.warning_count == 0:
        st.success("Data check completed. The workbook is ready.")
    elif validation_result.error_count == 0:
        st.warning("Please review the workbook before final calculation.")
    else:
        st.error("Please address the listed items before final calculation.")


def _render_calculation_section(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    if parsed_workbook is None or validation_result is None:
        st.info("Upload a file before running the calculation.")
        return

    st.write("Run the calculation after reviewing the file and confirming any required values.")
    if st.button("Run calculation", type="primary"):
        st.session_state["calculation_result"] = run_calculation(
            parsed_workbook,
            validation_result,
            st.session_state["manual_entry_store"],
        )


def _render_results_section(calculation_result: CalculationResult | None) -> None:
    if calculation_result is None:
        st.info("Run the calculation to view results.")
        return

    metrics = st.columns(4)
    metrics[0].metric("Rows prepared", calculation_result.summary.rows_prepared)
    metrics[1].metric("Ready rows", calculation_result.summary.ready_rows)
    metrics[2].metric("Status", calculation_result.summary.output_status)
    metrics[3].metric("Warnings", calculation_result.summary.warning_count)

    if not calculation_result.block_summary_frame.empty:
        st.write("Summary")
        st.dataframe(calculation_result.block_summary_frame, use_container_width=True, hide_index=True)

    if calculation_result.warnings:
        st.write("Items to review")
        warning_frame = pd.DataFrame(
            [
                {
                    "Block": warning.block_name,
                    "Message": warning.message,
                }
                for warning in calculation_result.warnings
            ]
        )
        st.dataframe(warning_frame, use_container_width=True, hide_index=True)

    st.write("Results by section")
    display_columns = {
        "employee_name": "Name",
        "position_name": "Position",
        "max_bonus": "Max bonus",
        "working_days": "Working days",
        "draft_component_total": "Calculated values",
        "draft_working_days_adjusted_value": "Working-days adjusted value",
        "draft_block_3_component_total": "Calculated values",
        "draft_block_4_act_bonus_example": "Calculated values",
        "calculated_bonus_amount": "Final output",
        "calculation_note": "Required confirmation",
        "manual_note": "Notes",
    }

    for index, block_result in enumerate(calculation_result.block_results, start=1):
        st.write(f"Block {index}")
        result_frame = pd.DataFrame(index=block_result.output_frame.index)
        for source_column, display_label in display_columns.items():
            if source_column in block_result.output_frame.columns and display_label not in result_frame.columns:
                result_frame[display_label] = block_result.output_frame[source_column]

        if "Calculated values" not in result_frame.columns:
            fallback_columns = [
                column_name
                for column_name in (
                    "draft_block_1_example_value",
                    "draft_block_2_example_value",
                    "draft_block_3_review_value",
                )
                if column_name in block_result.output_frame.columns
            ]
            for fallback_column in fallback_columns:
                result_frame["Calculated values"] = block_result.output_frame[fallback_column]
                break

        if result_frame.empty:
            st.info("No result rows are available for this section.")
        else:
            st.dataframe(result_frame, use_container_width=True, hide_index=True)

    if not calculation_result_is_exportable(calculation_result):
        st.info("A downloadable Excel file will be available once result rows are ready.")
        return

    try:
        export_package = build_export_package(calculation_result)
    except ValueError as exc:
        st.info(str(exc))
    except Exception:
        st.error("The Excel file could not be prepared. Please try again.")
    else:
        st.download_button(
            "Download Excel",
            data=export_package.content,
            file_name=export_package.file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def _render_advanced_view(parsed_workbook: ParsedWorkbook | None, validation_result: ValidationResult | None) -> None:
    workbook_sources: WorkbookSourceCollection = st.session_state["workbook_sources"]
    workbook_source: WorkbookSource | None = workbook_sources.primary_source
    if workbook_source is None:
        st.info("Upload a file to view source tables.")
        return

    top_left, top_right = st.columns(2)
    with top_left:
        st.write("Available worksheets")
        st.dataframe(
            pd.DataFrame({"Sheet name": workbook_source.sheet_names}),
            use_container_width=True,
            hide_index=True,
        )

        current_sheet = st.session_state.get("selected_sheet_name") or workbook_source.sheet_names[0]
        if current_sheet not in workbook_source.sheet_names:
            current_sheet = workbook_source.sheet_names[0]

        selected_sheet = st.selectbox(
            "Worksheet for raw preview",
            workbook_source.sheet_names,
            index=workbook_source.sheet_names.index(current_sheet),
            key="advanced_selected_sheet_name",
        )

        try:
            raw_preview_frame = load_sheet_preview(workbook_source, selected_sheet)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.write("Raw worksheet preview")
            if raw_preview_frame.empty:
                st.info("No preview rows are available for the selected worksheet.")
            else:
                st.dataframe(raw_preview_frame, use_container_width=True, hide_index=True)

    with top_right:
        if parsed_workbook is None:
            st.info("Upload a file to review parsed sections.")
            return

        st.write("Reference values")
        if parsed_workbook.reference_values:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Reference": reference_value.label,
                            "Cell": reference_value.cell_ref,
                            "Value": reference_value.value,
                        }
                        for reference_value in parsed_workbook.reference_values
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No reference values were found in the configured cells.")

        if validation_result is not None and not validation_result.validation_frame.empty:
            st.write("Validation summary")
            st.dataframe(validation_result.validation_frame, use_container_width=True, hide_index=True)

    if parsed_workbook is None or not parsed_workbook.regions:
        return

    st.write("Section details")
    region_names = [region.region_name for region in parsed_workbook.regions]
    selected_region = st.selectbox("Select section", region_names, index=0, key="advanced_selected_region")
    region = next(region for region in parsed_workbook.regions if region.region_name == selected_region)
    normalized_block = next(
        (block for block in parsed_workbook.normalized_blocks if block.block_name == selected_region),
        None,
    )
    block_config = next((block for block in APP_CONFIG.bonus_blocks if block.name == selected_region), None)

    info_columns = st.columns(4)
    info_columns[0].metric("Rows", len(region.frame.index))
    info_columns[1].metric("Detected columns", len(region.detected_columns))
    info_columns[2].metric("Expected fields", len(block_config.expected_columns) if block_config else 0)
    info_columns[3].metric("Header row", region.header_row)

    st.write("Detected source columns")
    st.write(", ".join(region.detected_columns) if region.detected_columns else "No columns detected")
    if region.duplicate_detected_columns:
        st.write(f"Repeated source columns: {', '.join(region.duplicate_detected_columns)}")
    if region.ambiguous_columns:
        st.write(f"Columns needing confirmation: {', '.join(region.ambiguous_columns)}")

    raw_col, normalized_col = st.columns(2)
    with raw_col:
        st.write("Source preview")
        st.dataframe(region.frame, use_container_width=True, hide_index=True)

    with normalized_col:
        st.write("Prepared data preview")
        if normalized_block is None:
            st.info("No prepared data preview is available for this section.")
        else:
            label_frame = pd.DataFrame(
                [
                    {
                        "Internal field": field_name,
                        "Source column": normalized_block.field_labels.get(field_name, ""),
                        "Field type": "Shared" if field_name in normalized_block.shared_fields else "Block-specific",
                    }
                    for field_name in normalized_block.normalized_frame.columns
                    if field_name
                    not in {"block_key", "block_name", "source_sheet", "header_row", "source_row_number"}
                ]
            )
            st.dataframe(normalized_block.normalized_frame, use_container_width=True, hide_index=True)
            st.write("Field mapping")
            st.dataframe(label_frame, use_container_width=True, hide_index=True)


def _render_settings() -> None:
    st.write("Current settings")
    top_metrics = st.columns(4)
    top_metrics[0].metric("Bonus blocks", len(APP_CONFIG.bonus_blocks))
    top_metrics[1].metric("Reference cells", len(APP_CONFIG.reference_cells))
    top_metrics[2].metric("Draft formulas", sum(1 for item in APP_SETTINGS.block_settings if item.draft_formula_enabled))
    top_metrics[3].metric(
        "Entry options",
        sum(
            1
            for value in (
                APP_SETTINGS.manual_overrides.allow_manual_reference_values,
                APP_SETTINGS.manual_overrides.allow_manual_targets,
                APP_SETTINGS.manual_overrides.allow_manual_adjustments,
                APP_SETTINGS.manual_overrides.allow_block_specific_values,
                APP_SETTINGS.manual_overrides.allow_future_additional_file_values,
            )
            if value
        ),
    )

    with st.expander("Thresholds", expanded=True):
        threshold_frame = pd.DataFrame(
            [
                {"Setting": "Suspicious row count limit", "Value": APP_SETTINGS.thresholds.suspicious_row_count_limit},
                {"Setting": "Date review year from", "Value": APP_SETTINGS.thresholds.date_review_year_min},
                {"Setting": "Date review year to", "Value": APP_SETTINGS.thresholds.date_review_year_max},
            ]
        )
        st.dataframe(threshold_frame, use_container_width=True, hide_index=True)

    with st.expander("Percentages", expanded=False):
        percentage_frame = pd.DataFrame(
            [
                {"Setting": "Block 1 Personal", "Value": f"{APP_SETTINGS.percentages.block_1_personal:.1f}%"},
                {"Setting": "Block 1 SPR", "Value": f"{APP_SETTINGS.percentages.block_1_spr:.1f}%"},
                {"Setting": "Block 1 SPORH", "Value": f"{APP_SETTINGS.percentages.block_1_sporh:.1f}%"},
                {"Setting": "Block 2 Personal", "Value": f"{APP_SETTINGS.percentages.block_2_personal:.1f}%"},
                {"Setting": "Block 2 SPR", "Value": f"{APP_SETTINGS.percentages.block_2_spr:.1f}%"},
                {"Setting": "Block 2 SPORH", "Value": f"{APP_SETTINGS.percentages.block_2_sporh:.1f}%"},
                {"Setting": "Block 3 Checkpoint", "Value": f"{APP_SETTINGS.percentages.block_3_checkpoint:.1f}%"},
                {"Setting": "Block 3 Google review", "Value": f"{APP_SETTINGS.percentages.block_3_google_review:.1f}%"},
                {"Setting": "Block 4 Personal", "Value": f"{APP_SETTINGS.percentages.block_4_personal:.1f}%"},
                {"Setting": "Block 4 Sales leads", "Value": f"{APP_SETTINGS.percentages.block_4_sales_leads:.1f}%"},
                {"Setting": "Block 4 TW Adh", "Value": f"{APP_SETTINGS.percentages.block_4_tw_adh:.1f}%"},
            ]
        )
        st.dataframe(percentage_frame, use_container_width=True, hide_index=True)

    with st.expander("Reference values", expanded=False):
        reference_frame = pd.DataFrame(
            [
                {"Setting": "Primary working-days reference", "Value": APP_SETTINGS.references.primary_working_days_reference},
                {"Setting": "Fallback references", "Value": ", ".join(APP_SETTINGS.references.fallback_reference_labels)},
            ]
        )
        st.dataframe(reference_frame, use_container_width=True, hide_index=True)

    with st.expander("Block settings", expanded=False):
        block_settings_frame = pd.DataFrame(
            [
                {
                    "Block": block_setting.block_label,
                    "Draft calculation": "Yes" if block_setting.draft_formula_enabled else "No",
                    "Reference value": block_setting.reference_label or "Not required",
                    "Manual target": "Yes" if block_setting.supports_manual_target else "No",
                    "Manual adjustment": "Yes" if block_setting.supports_manual_adjustment else "No",
                    "Additional values": "Yes" if block_setting.supports_extra_values else "No",
                    "Notes": block_setting.notes,
                }
                for block_setting in APP_SETTINGS.block_settings
            ]
        )
        st.dataframe(block_settings_frame, use_container_width=True, hide_index=True)

    with st.expander("Manual override behavior", expanded=False):
        manual_override_frame = pd.DataFrame(
            [
                {"Setting": "Manual reference values", "Value": "Enabled" if APP_SETTINGS.manual_overrides.allow_manual_reference_values else "Disabled"},
                {"Setting": "Manual targets", "Value": "Enabled" if APP_SETTINGS.manual_overrides.allow_manual_targets else "Disabled"},
                {"Setting": "Manual adjustments", "Value": "Enabled" if APP_SETTINGS.manual_overrides.allow_manual_adjustments else "Disabled"},
                {"Setting": "Block-specific values", "Value": "Enabled" if APP_SETTINGS.manual_overrides.allow_block_specific_values else "Disabled"},
                {"Setting": "Future additional file values", "Value": "Enabled" if APP_SETTINGS.manual_overrides.allow_future_additional_file_values else "Disabled"},
            ]
        )
        st.dataframe(manual_override_frame, use_container_width=True, hide_index=True)

    with st.expander("Additional file support", expanded=False):
        additional_source_frame = pd.DataFrame(
            [
                {"Setting": "Current workflow", "Value": "Primary workbook only"},
                {"Setting": "Additional workbook support", "Value": "Available for future update"},
                {"Setting": "Merge behavior", "Value": "Not yet enabled"},
            ]
        )
        st.dataframe(additional_source_frame, use_container_width=True, hide_index=True)

    st.info("Settings are available for review and can be updated when business rules change.")


def run_app() -> None:
    _initialize_state()
    _render_header()

    parsed_workbook: ParsedWorkbook | None = st.session_state["parsed_workbook"]
    validation_result: ValidationResult | None = st.session_state["validation_result"]
    calculation_result: CalculationResult | None = st.session_state["calculation_result"]

    _render_overview(parsed_workbook, validation_result)

    tabs = st.tabs(
        [
            "Upload File",
            "Review Data",
            "Enter Missing Values",
            "Check Data",
            "Run Calculation",
            "Results",
            "Advanced View",
            "Settings",
        ]
    )

    with tabs[0]:
        _render_upload_section()
    with tabs[1]:
        _render_review_section(st.session_state["parsed_workbook"], st.session_state["validation_result"])
    with tabs[2]:
        _render_validation_section(st.session_state["parsed_workbook"], st.session_state["validation_result"])
    with tabs[3]:
        _render_check_section(st.session_state["parsed_workbook"], st.session_state["validation_result"])
    with tabs[4]:
        _render_calculation_section(st.session_state["parsed_workbook"], st.session_state["validation_result"])
    with tabs[5]:
        _render_results_section(st.session_state["calculation_result"])
    with tabs[6]:
        _render_advanced_view(st.session_state["parsed_workbook"], st.session_state["validation_result"])
    with tabs[7]:
        _render_settings()
