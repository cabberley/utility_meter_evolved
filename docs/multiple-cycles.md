# Multiple reset cycles from one source

[All guides](README.md) · [Cost meters](costs.md) · [Schedules](schedules.md)

## Daily, monthly, and yearly electricity

**Goal:** create independent reporting periods without repeating the source configuration.

1. Create a **Utility Meter Next Gen** helper named `House electricity`.
2. Choose your cumulative energy source.
3. Optionally select a numeric rate sensor or `input_number` for costs.
4. Select **Create Multiple Predefined reset cycle Meters** and submit.
5. Choose **Daily**, **Monthly**, and **Yearly** in **Predefined Reset Cycle**, then submit. Select at least two cycles; the current implementation cannot load a multiple-cycle helper with only one selected cycle.
6. In the next form:
   - Leave tariffs empty unless you want [tariff splitting](tariffs.md).
   - Leave Delta Values and Net Consumption off for cumulative import.
   - Set Periodically resetting according to your source.
   - Leave consumption calibration at `0`.
   - For costs, enable **Create a separate Calculation Sensor** and set the unit adjustment factor.
7. Submit, then inspect the resulting entities.

Each selected cycle has its own consumption sensor and, if enabled, its own **Calculated** sensor. For this example without tariffs, expect **3 consumption sensors**, or **6 sensors** with separate calculation sensors enabled.

The supported intervals range from 5, 10, 15, 20, and 30 minutes through hourly, daily, weekly, monthly, every two months, quarterly, half-yearly, and yearly.

## Understand independent periods

All meters process changes from the same source, but each resets on its own schedule.

- At midnight, the daily meter begins a new cycle.
- On the first of the month, the monthly meter begins a new cycle.
- On January 1, the yearly meter begins a new cycle.

The monthly meter is **not a sum of the daily meter's states**; the yearly meter is not a sum of monthly states. They each collect directly from the source. All initial periods are partial if created mid-period.

Multiple-cycle configurations do not offer an offset. For a non-calendar billing date or a daily reset at a particular time, use a separate [CRON meter](schedules.md).

## Standing charge on the daily meter only

When a calculation input is selected:

1. Enter your fixed daily charge under **Calibration Value for Calculation**, or select a charge entity under **Calibration Sensor for Calculation**.
2. Select **Daily** under **Apply Calculation Calibration to which Predefined Cycle?**.
3. Leave consumption calibration at `0`, then submit.

Only the selected cycle receives calculation calibration. A `0.60` daily charge makes the daily calculation start at `0.60`; monthly and yearly calculations start at zero and collect consumption costs only.

**Important:** monthly and yearly meters do not inherit charges added to daily meters. If you need longer-period costs including every daily charge, use a separate aggregation appropriate to your reporting requirements. Do not put a daily charge into monthly calibration and expect it to be multiplied by the days in the month.

Consumption calibration has its own independent **Apply Calibration to which Predefined Cycle?** selection. A nonzero calibration needs the intended cycle explicitly selected.

## Combine cycles and tariffs

For **Daily**, **Monthly**, and **Yearly**, with tariffs `peak`, `off_peak`, and `total`:

- Consumption sensors: `3 cycles × 3 tariffs = 9`.
- With separate calculations enabled: another `9` calculated sensors.
- Tariff control: one `select` entity shared by all cycles.

Changing that selector switches all normal tariff meters together. Total meters remain collecting. Leave calibration at zero when using tariffs: in the current implementation, the selected cycle's individual tariff meters also receive calibration at initialization/reset. Use a separate tariff-free helper for a standing charge; see the [tariff limitation](tariffs.md#check-totals-and-charges).

Only select periods you will use; many cycles and tariffs can create a large entity list.

## Reconfigure

Open the helper's options to add/remove cycles, update sources, edit existing tariffs, or enable/disable separate calculation sensors. The configuration stays a multiple-predefined-cycle setup; it does not switch to CRON.

**Current limitation:** retain at least **two actual reset cycles**. A multiple-cycle helper with only one selected cycle fails to load; an empty selection or **No cycle** is not a valid multiple-cycle setup either. If you only need one period, create a single-predefined helper instead.

Before removing a cycle or tariff, record the values you need and check dashboards and automations referencing its entities. New entities do not reconstruct earlier data. After changing the selected cycles, recheck both calibration target selections and `next_reset` on each meter.
