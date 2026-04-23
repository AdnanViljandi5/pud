# Bonus Calculation Tool

## Overview

This project is a local Streamlit application for reviewing a fixed-format Excel workbook, validating the data, capturing manual confirmations, preparing bonus calculation results, and exporting the output as a new Excel workbook.

The app is designed for one internal user who works with a known workbook format. The user interface stays fixed while the workbook is interpreted through configurable parsing and mapping logic behind the scenes.

## How to run the app

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The app opens locally in Streamlit and expects one Excel workbook upload in the current workflow.

## Project structure

- `app.py`
  Starts the Streamlit app and calls the main UI module.
- `business_tool/ui.py`
  Contains the Streamlit interface, session-state handling, tab rendering, upload flow, and download button behavior.
- `business_tool/config.py`
  Defines the expected workbook layout, top reference cells, and the four configured bonus blocks.
- `business_tool/parsing.py`
  Loads the Excel workbook, previews sheets, reads the top reference area, parses each block separately, and builds normalized internal block data.
- `business_tool/validation.py`
  Runs workbook and parsed-data checks and returns user-facing `Error`, `Warning`, and `Information` messages.
- `business_tool/manual_entries.py`
  Builds and sanitizes stored manual inputs such as reference values, confirmed targets, adjustments, and notes.
- `business_tool/calculation.py`
  Contains the calculation engine, including separate calculation functions for each block and the combined result assembly.
- `business_tool/export_output.py`
  Creates the downloadable Excel export in memory without modifying the uploaded source workbook.
- `business_tool/settings_config.py`
  Stores maintainable business settings such as thresholds, percentages, references, and manual override behavior.
- `business_tool/source_manager.py`
  Holds the source-loading structure for the current primary workbook and the future second-workbook extension point.
- `business_tool/models.py`
  Defines shared data models for parsed workbook content, validation, manual entries, calculations, and export packages.

## Current workbook interpretation

The workbook is currently treated as a fixed-layout file.

- Expected default sheet name: `Bonus Input`
- Expected top reference area: cells around rows 3 to 6
- Expected blocks:
  - Block 1 starts at row 8
  - Block 2 starts at row 12
  - Block 3 starts at row 20
  - Block 4 starts at row 28

The parser does not assume a single continuous table. Each bonus block is parsed separately using the configured start row, start column, expected headers, and internal column mappings from `business_tool/config.py`.

If the workbook changes later, update the configuration rather than rewriting the UI.

## Top reference area

The parser currently captures these configured reference cells when values are present:

- `E3`
- `E4`
- `E5`
- `E6`
- `F4`
- `F5`
- `F6`
- `G5`
- `G6`
- `H5`
- `H6`
- `I5`
- `I6`

These values are stored as top-level reference values only. Their exact business meaning is not assumed unless calculation logic explicitly uses them.

## Bonus blocks

### Block 1

Configured as a bonus table with shared employee fields plus these weighted components:

- `Personal 30%`
- `SPR 35%`
- `SPORH 35%`

The current calculation engine supports a limited draft weighted-component pattern and a working-days adjustment using the known example that references `E4`.

### Block 2

Configured as a bonus table with shared employee fields plus these weighted components:

- `Personal 50%`
- `SPR 25%`
- `SPORH 25%`

The current calculation engine supports a limited draft weighted-component pattern and a working-days adjustment using the same reference approach as Block 1.

### Block 3

Configured as a bonus table with these main block-specific inputs:

- `SL checkpoint compliance 50%`
- `Google review/personal for Kaur 50%`
- `Insurance extra sale bonus`

The current engine prepares a component review value and includes the insurance extra sale bonus as an additional component, but it does not finalize the block result because the final rule treatment still needs confirmation.

### Block 4

Configured as a more detailed block with several additional fields, including repeated header names in the draft workbook:

- `Max bonus act WD` appears twice
- `Sales leads payout` appears twice

The parser keeps those columns separately with safe internal names. The calculation engine supports the known draft `Act bonus` example through isolated field mappings, but the exact meaning of some repeated columns still needs confirmation.

## Normalized internal data

The app keeps raw parsed block data and normalized internal block data separately.

- Raw data is preserved for advanced review and maintenance.
- Normalized data is used for validation, calculations, and export.
- The app does not force all four blocks into one incorrect schema.

Each normalized block includes:

- shared employee and bonus fields where available
- block-specific fields for that block only
- source metadata such as sheet name and row number
- user-friendly labels for display and export

## Validation

Validation is implemented in `business_tool/validation.py`.

The app currently checks for:

- missing expected sheets
- unreadable or empty uploads
- incomplete or missing header rows
- missing expected columns
- duplicate detected headers
- ambiguous repeated columns in Block 4
- blank important-looking fields
- unclear date values
- suspicious row counts
- missing configured reference cells

Validation results are returned with three severities:

- `Error`
- `Warning`
- `Information`

## Calculations

Calculations are implemented in `business_tool/calculation.py`.

The engine is separated from the UI and currently uses:

- parsed normalized block data
- top reference values
- manual inputs
- validation state

Main calculation entry points:

- `run_calculation(...)`
- `run_calculation_engine(...)`
- `calculate_block_1(...)`
- `calculate_block_2(...)`
- `calculate_block_3(...)`
- `calculate_block_4(...)`

## Rules that still need confirmation

The following parts are intentionally isolated because the business rules are not fully confirmed yet:

- the exact business meaning of the top reference cells
- the final formula interpretation for Block 1 and Block 2 beyond the known weighted working-days example pattern
- the final result logic for Block 3
- the exact field meaning of repeated or similar Block 4 columns
- the final export scope if another system later requires a stricter output format

When a value cannot be finalized safely, the app keeps the result in a review state and surfaces a user-facing confirmation message instead of silently fabricating logic.

## How to update mappings later

If the workbook layout changes:

1. Update `business_tool/config.py`.
2. Adjust:
   - sheet name
   - header rows
   - start columns
   - expected column captions
   - internal column names
   - shared fields
3. If the meaning of a column changes, update both:
   - `business_tool/config.py` for mapping
   - `business_tool/calculation.py` for formula use
4. Re-run the app and review the `Advanced View` tab to confirm the new mapping.

## How to update formulas later

When business rules are confirmed:

1. Update the relevant block function in `business_tool/calculation.py`.
2. Keep uncertain or workbook-specific field mappings isolated in clearly named constants or helper sections.
3. If new thresholds or percentages are needed, update `business_tool/settings_config.py`.
4. If the result workbook needs different output columns, update `business_tool/export_output.py`.

## Export behavior

The export is created as a new workbook in memory and never overwrites the uploaded file.

Current export logic lives in `business_tool/export_output.py` and is designed to be easy to adjust later. At the moment it includes only clean result output intended for sharing, not raw parsing tables.

## Future second Excel support

The current workflow uses only one uploaded workbook, but the structure for a second workbook has been prepared.

Relevant files:

- `business_tool/source_manager.py`
- `business_tool/parsing.py`
- `business_tool/models.py`
- `business_tool/manual_entries.py`

Future second-source work should be added in this order:

1. Load the additional workbook through `source_manager.py`.
2. Parse it separately rather than mixing it into the primary parser.
3. Add second-source mapping and merge rules in `merge_workbook_sources(...)`.
4. Extend calculations only after the source-to-source relationships are confirmed.

This keeps the current one-file workflow stable while leaving a clear insertion point for future expansion.
