from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceCellConfig:
    cell_ref: str
    sheet_name: str
    label: str


@dataclass(frozen=True, slots=True)
class BonusBlockConfig:
    key: str
    name: str
    sheet_name: str
    header_row: int
    start_column: str
    expected_columns: tuple[str, ...]
    internal_columns: tuple[str, ...]
    shared_fields: tuple[str, ...]
    data_end_row: int | None = None
    max_data_rows: int = 25


@dataclass(frozen=True, slots=True)
class AppConfig:
    page_title: str
    upload_label: str
    output_file_name: str
    reference_cells: tuple[ReferenceCellConfig, ...]
    bonus_blocks: tuple[BonusBlockConfig, ...]


DEFAULT_SHEET_NAME = "Bonus Input"


APP_CONFIG = AppConfig(
    page_title="Bonus Calculator",
    upload_label="Upload file",
    output_file_name="bonus_calculation_output.xlsx",
    reference_cells=(
        ReferenceCellConfig(cell_ref="E3", sheet_name=DEFAULT_SHEET_NAME, label="E3"),
        ReferenceCellConfig(cell_ref="E4", sheet_name=DEFAULT_SHEET_NAME, label="E4"),
        ReferenceCellConfig(cell_ref="E5", sheet_name=DEFAULT_SHEET_NAME, label="E5"),
        ReferenceCellConfig(cell_ref="E6", sheet_name=DEFAULT_SHEET_NAME, label="E6"),
        ReferenceCellConfig(cell_ref="F4", sheet_name=DEFAULT_SHEET_NAME, label="F4"),
        ReferenceCellConfig(cell_ref="F5", sheet_name=DEFAULT_SHEET_NAME, label="F5"),
        ReferenceCellConfig(cell_ref="F6", sheet_name=DEFAULT_SHEET_NAME, label="F6"),
        ReferenceCellConfig(cell_ref="G5", sheet_name=DEFAULT_SHEET_NAME, label="G5"),
        ReferenceCellConfig(cell_ref="G6", sheet_name=DEFAULT_SHEET_NAME, label="G6"),
        ReferenceCellConfig(cell_ref="H5", sheet_name=DEFAULT_SHEET_NAME, label="H5"),
        ReferenceCellConfig(cell_ref="H6", sheet_name=DEFAULT_SHEET_NAME, label="H6"),
        ReferenceCellConfig(cell_ref="I5", sheet_name=DEFAULT_SHEET_NAME, label="I5"),
        ReferenceCellConfig(cell_ref="I6", sheet_name=DEFAULT_SHEET_NAME, label="I6"),
    ),
    bonus_blocks=(
        BonusBlockConfig(
            key="bonus_block_1",
            name="Bonus block 1",
            sheet_name=DEFAULT_SHEET_NAME,
            header_row=8,
            start_column="A",
            expected_columns=(
                "Number",
                "Name",
                "Team name",
                "Position",
                "Manager",
                "Date started",
                "Max bonus",
                "Personal 30%",
                "SPR 35%",
                "SPORH 35%",
                "Working days",
                "Total bonus",
                "Remarks",
            ),
            internal_columns=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "personal_component_30",
                "spr_component_35",
                "sporh_component_35",
                "working_days",
                "total_bonus",
                "remarks",
            ),
            shared_fields=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "working_days",
                "total_bonus",
                "remarks",
            ),
        ),
        BonusBlockConfig(
            key="bonus_block_2",
            name="Bonus block 2",
            sheet_name=DEFAULT_SHEET_NAME,
            header_row=12,
            start_column="A",
            expected_columns=(
                "Number",
                "Name",
                "Team name",
                "Position",
                "Manager",
                "Date started",
                "Max bonus",
                "Personal 50%",
                "SPR 25%",
                "SPORH 25%",
                "Working days",
                "Total bonus",
                "Remarks",
            ),
            internal_columns=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "personal_component_50",
                "spr_component_25",
                "sporh_component_25",
                "working_days",
                "total_bonus",
                "remarks",
            ),
            shared_fields=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "working_days",
                "total_bonus",
                "remarks",
            ),
        ),
        BonusBlockConfig(
            key="bonus_block_3",
            name="Bonus block 3",
            sheet_name=DEFAULT_SHEET_NAME,
            header_row=20,
            start_column="A",
            expected_columns=(
                "Number",
                "Name",
                "Team name",
                "Position",
                "Manager",
                "Date started",
                "Max bonus",
                "SL checkpoint compliance 50%",
                "Google review/personal for Kaur 50%",
                "Insurance extra sale bonus",
                "Working days",
                "Total bonus",
                "Remarks",
            ),
            internal_columns=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "sl_checkpoint_compliance_50",
                "google_review_or_personal_for_kaur_50",
                "insurance_extra_sale_bonus",
                "working_days",
                "total_bonus",
                "remarks",
            ),
            shared_fields=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "working_days",
                "total_bonus",
                "remarks",
            ),
        ),
        BonusBlockConfig(
            key="bonus_block_4",
            name="Bonus block 4",
            sheet_name=DEFAULT_SHEET_NAME,
            header_row=28,
            start_column="A",
            expected_columns=(
                "Number",
                "Name",
                "Team name",
                "Position",
                "Manager",
                "Date started",
                "Max bonus",
                "Bonus per WD",
                "Max bonus act WD",
                "Max bonus act WD",
                "Act personal 33.3%",
                "Sales leads 33.3% max",
                "Act sales leads",
                "TW Adh target %",
                "TW Adh actual %",
                "NEW! TW Adh (33.3%) sum",
                "Working days",
                "Total bonus",
                "Act bonus",
                "Feb working days",
                "Target sales lead",
                "Actual sales leads",
                "Sales leads payout",
                "Sales leads payout",
            ),
            internal_columns=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "bonus_per_working_day",
                "max_bonus_actual_working_days_1",
                "max_bonus_actual_working_days_2",
                "actual_personal_component_33_3",
                "sales_leads_component_max_33_3",
                "actual_sales_leads_metric",
                "tw_adh_target_percent",
                "tw_adh_actual_percent",
                "tw_adh_component_sum_33_3",
                "working_days",
                "total_bonus",
                "actual_bonus",
                "feb_working_days",
                "target_sales_lead",
                "actual_sales_leads_count",
                "sales_leads_payout_1",
                "sales_leads_payout_2",
            ),
            shared_fields=(
                "employee_number",
                "employee_name",
                "team_name",
                "position_name",
                "manager_name",
                "date_started",
                "max_bonus",
                "working_days",
                "total_bonus",
            ),
            max_data_rows=30,
        ),
    ),
)

# Workbook settings are intentionally configurable because the draft file may
# shift slightly when the latest business workbook is received.
# Some block 4 internal names remain intentionally neutral until the exact
# business meaning of duplicate draft columns is confirmed.
