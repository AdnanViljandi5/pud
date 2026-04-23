from __future__ import annotations

from typing import BinaryIO

from business_tool.models import ParsedWorkbook, WorkbookSource, WorkbookSourceCollection
from business_tool.parsing import load_workbook_source, parse_workbook


PRIMARY_SOURCE_KEY = "primary_workbook"
SECONDARY_SOURCE_KEY = "secondary_workbook"


def load_primary_workbook(uploaded_file: BinaryIO, preview_row_limit: int = 25) -> WorkbookSource:
    return load_workbook_source(
        uploaded_file,
        preview_row_limit=preview_row_limit,
        source_key=PRIMARY_SOURCE_KEY,
        source_label="Primary workbook",
    )


def load_secondary_workbook(uploaded_file: BinaryIO, preview_row_limit: int = 25) -> WorkbookSource:
    return load_workbook_source(
        uploaded_file,
        preview_row_limit=preview_row_limit,
        source_key=SECONDARY_SOURCE_KEY,
        source_label="Additional workbook",
    )


def build_source_collection(primary_source: WorkbookSource | None) -> WorkbookSourceCollection:
    return WorkbookSourceCollection(primary_source=primary_source, secondary_source=None)


def parse_primary_workbook(primary_source: WorkbookSource) -> ParsedWorkbook:
    return parse_workbook(primary_source)


def merge_workbook_sources(
    primary_workbook: ParsedWorkbook,
    secondary_workbook: ParsedWorkbook | None,
) -> ParsedWorkbook:
    # Future maintainers:
    # Insert second-source mapping and merge behavior here after the structure of
    # the additional workbook is confirmed. The current one-file workflow should
    # continue to use the primary workbook without modification.
    if secondary_workbook is None:
        return primary_workbook
    return primary_workbook
