# Maintenance Notes

## First places to check

- Workbook structure changed: `business_tool/config.py`
- Parser failed or previews look wrong: `business_tool/parsing.py`
- Data checks need adjustment: `business_tool/validation.py`
- Manual-entry behavior needs adjustment: `business_tool/manual_entries.py`
- Formula behavior changed: `business_tool/calculation.py`
- Export columns or sheets changed: `business_tool/export_output.py`
- Business defaults changed: `business_tool/settings_config.py`
- Future additional workbook work: `business_tool/source_manager.py`

## Safe update workflow

1. Update configuration before changing UI code.
2. Keep parsing changes separate from calculation changes.
3. Use the `Advanced View` tab to confirm:
   - raw sheet preview
   - detected columns
   - normalized parsed preview
   - reference values
4. Use the `Check Data` tab to confirm validation behavior.
5. Run the calculation and confirm only the expected blocks produce results.
6. Download the Excel file and review worksheet names and headers.

## Common maintenance tasks

### Workbook rows or headers moved

- Update the relevant `BonusBlockConfig` in `business_tool/config.py`.
- Confirm the expected sheet name if it also changed.
- Check the top reference cell list if the reference area moved.

### A mapped column name needs to change

- Update `expected_columns` and `internal_columns` together in `business_tool/config.py`.
- If the column is used in formulas, update the matching references in `business_tool/calculation.py`.

### A business rule becomes confirmed

- Replace the draft or review-only logic in the relevant `calculate_block_*` function.
- Keep comments for any remaining uncertain parts.
- Update `business_tool/settings_config.py` if the rule introduces a new default percentage or threshold.

### Block 4 is clarified

- Review duplicate headers in `business_tool/config.py`.
- Review isolated field usage in `business_tool/calculation.py`, especially the Block 4 draft field mapping.
- Confirm validation wording in `business_tool/validation.py` if ambiguity is resolved.

### Export requirements change

- Update exported columns in `business_tool/export_output.py`.
- Keep export-only naming changes there rather than renaming internal model fields.

## Stability reminders

- Do not make the UI depend on workbook shape.
- Keep the tab layout fixed.
- Preserve raw parsed data separately from normalized data.
- Do not overwrite the uploaded workbook.
- Keep second-workbook support layered on top of the existing primary parser.
