from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThresholdSettings:
    suspicious_row_count_limit: int
    date_review_year_min: int
    date_review_year_max: int


@dataclass(frozen=True, slots=True)
class PercentageSettings:
    block_1_personal: float
    block_1_spr: float
    block_1_sporh: float
    block_2_personal: float
    block_2_spr: float
    block_2_sporh: float
    block_3_checkpoint: float
    block_3_google_review: float
    block_4_personal: float
    block_4_sales_leads: float
    block_4_tw_adh: float


@dataclass(frozen=True, slots=True)
class ReferenceSettings:
    primary_working_days_reference: str
    fallback_reference_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManualOverrideSettings:
    allow_manual_reference_values: bool
    allow_manual_targets: bool
    allow_manual_adjustments: bool
    allow_block_specific_values: bool
    allow_future_additional_file_values: bool


@dataclass(frozen=True, slots=True)
class BlockCalculationSetting:
    block_key: str
    block_label: str
    draft_formula_enabled: bool
    requires_reference_value: bool
    reference_label: str | None
    supports_manual_target: bool
    supports_manual_adjustment: bool
    supports_extra_values: bool
    notes: str


@dataclass(frozen=True, slots=True)
class AppSettings:
    thresholds: ThresholdSettings
    percentages: PercentageSettings
    references: ReferenceSettings
    manual_overrides: ManualOverrideSettings
    block_settings: tuple[BlockCalculationSetting, ...]


APP_SETTINGS = AppSettings(
    thresholds=ThresholdSettings(
        suspicious_row_count_limit=25,
        date_review_year_min=2020,
        date_review_year_max=2035,
    ),
    percentages=PercentageSettings(
        block_1_personal=30.0,
        block_1_spr=35.0,
        block_1_sporh=35.0,
        block_2_personal=50.0,
        block_2_spr=25.0,
        block_2_sporh=25.0,
        block_3_checkpoint=50.0,
        block_3_google_review=50.0,
        block_4_personal=33.3,
        block_4_sales_leads=33.3,
        block_4_tw_adh=33.3,
    ),
    references=ReferenceSettings(
        primary_working_days_reference="E4",
        fallback_reference_labels=("E3", "E5", "E6"),
    ),
    manual_overrides=ManualOverrideSettings(
        allow_manual_reference_values=True,
        allow_manual_targets=True,
        allow_manual_adjustments=True,
        allow_block_specific_values=True,
        allow_future_additional_file_values=True,
    ),
    block_settings=(
        BlockCalculationSetting(
            block_key="bonus_block_1",
            block_label="Block 1",
            draft_formula_enabled=True,
            requires_reference_value=True,
            reference_label="E4",
            supports_manual_target=True,
            supports_manual_adjustment=True,
            supports_extra_values=True,
            notes="Weighted component draft calculation is available.",
        ),
        BlockCalculationSetting(
            block_key="bonus_block_2",
            block_label="Block 2",
            draft_formula_enabled=True,
            requires_reference_value=True,
            reference_label="E4",
            supports_manual_target=True,
            supports_manual_adjustment=True,
            supports_extra_values=True,
            notes="Weighted component draft calculation is available.",
        ),
        BlockCalculationSetting(
            block_key="bonus_block_3",
            block_label="Block 3",
            draft_formula_enabled=False,
            requires_reference_value=False,
            reference_label=None,
            supports_manual_target=True,
            supports_manual_adjustment=True,
            supports_extra_values=True,
            notes="Insurance extra sale bonus is included in draft component review only.",
        ),
        BlockCalculationSetting(
            block_key="bonus_block_4",
            block_label="Block 4",
            draft_formula_enabled=True,
            requires_reference_value=False,
            reference_label=None,
            supports_manual_target=True,
            supports_manual_adjustment=True,
            supports_extra_values=True,
            notes="Draft Act bonus example is available and duplicate columns still need confirmation.",
        ),
    ),
)

# Future maintainers:
# Keep these settings business-focused and stable for the user interface.
# If settings later become editable in the app or stored outside code, this
# module should remain the central structure for default values.
