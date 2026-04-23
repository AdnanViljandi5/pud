from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(slots=True)
class WorkbookSummary:
    sheet_count: int
    region_count: int
    row_count: int


@dataclass(slots=True)
class ReferenceValue:
    label: str
    cell_ref: str
    value: object


@dataclass(slots=True)
class ParsedRegion:
    region_name: str
    frame: pd.DataFrame
    detected_columns: list[str]
    expected_columns: list[str]
    missing_expected_columns: list[str]
    duplicate_detected_columns: list[str]
    ambiguous_columns: list[str]
    source_sheet: str
    header_row: int


@dataclass(slots=True)
class NormalizedBlock:
    block_key: str
    block_name: str
    normalized_frame: pd.DataFrame
    shared_fields: tuple[str, ...]
    specific_fields: tuple[str, ...]
    field_labels: dict[str, str]
    source_sheet: str
    header_row: int


@dataclass(slots=True)
class ParsedWorkbook:
    reference_values: list[ReferenceValue]
    regions: list[ParsedRegion]
    normalized_blocks: list[NormalizedBlock]
    combined_frame: pd.DataFrame
    review_frame: pd.DataFrame
    normalized_combined_frame: pd.DataFrame
    summary: WorkbookSummary
    issues: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkbookSource:
    source_key: str
    source_label: str
    file_name: str
    file_bytes: bytes
    sheet_names: list[str]
    preview_row_limit: int


@dataclass(slots=True)
class WorkbookSourceCollection:
    primary_source: WorkbookSource | None = None
    secondary_source: WorkbookSource | None = None


@dataclass(slots=True)
class ValidationItem:
    severity: str
    section: str
    message: str


@dataclass(slots=True)
class ValidationResult:
    is_ready: bool
    items: list[ValidationItem]
    messages: list[str]
    validation_frame: pd.DataFrame
    error_count: int
    warning_count: int
    information_count: int


@dataclass(slots=True)
class ManualBlockEntry:
    confirmed_target: str = ""
    manual_adjustment: float = 0.0
    extra_value: str = ""
    note: str = ""


@dataclass(slots=True)
class ManualEntryStore:
    reference_values: dict[str, str] = field(default_factory=dict)
    block_entries: dict[str, ManualBlockEntry] = field(default_factory=dict)
    future_source_values: dict[str, str] = field(default_factory=dict)
    general_notes: str = ""
    adjustment_notes: str = ""


@dataclass(slots=True)
class CalculationSummary:
    rows_prepared: int
    ready_rows: int
    output_status: str
    warning_count: int


@dataclass(slots=True)
class CalculationWarning:
    block_name: str
    message: str


@dataclass(slots=True)
class BlockCalculationResult:
    block_key: str
    block_name: str
    output_frame: pd.DataFrame
    warning_messages: list[str]
    rows_prepared: int
    status: str


@dataclass(slots=True)
class CalculationResult:
    block_results: list[BlockCalculationResult]
    warnings: list[CalculationWarning]
    block_summary_frame: pd.DataFrame
    summary: CalculationSummary
    output_frame: pd.DataFrame


@dataclass(slots=True)
class ExportPackage:
    file_name: str
    content: bytes
