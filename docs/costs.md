# Cost meters and standing charges

[All guides](README.md) · [Next: tariffs](tariffs.md)

## Daily electricity cost at a fixed rate

**Goal:** expose both consumption today and cost today.

You need:

- A cumulative energy source, for example `sensor.grid_import_energy` in kWh.
- A numeric rate entity, for example `input_number.electricity_rate` with state `0.25` and unit `GBP/kWh`.

To create a fixed rate, open **Settings → Devices & services → Helpers → Create helper → Number**, set a range that covers your price and a suitable step (for example `0.0001`), and set the current value to your rate. Use your actual currency and rate, including tax if that is what you want to track.

1. Create a **Utility Meter Next Gen** helper named `Electricity cost today`.
2. Select the energy source as **Input sensor for Metering**.
3. Select the rate entity as **Input Calculation Sensor**.
4. Choose **Create using a Predefined reset cycle** and submit.
5. Set the following:

| Setting | Value |
| --- | --- |
| **Predefined Reset Cycle** | Daily |
| **Offset** | All zero |
| **Create a separate Calculation Sensor** | On |
| **Adjustment factor for the calculation sensor** | `1` for kWh and GBP/kWh |
| **Calibration Value for Calculation** | `0` initially, or your daily fixed charge |
| **Calibration Value for Consumption** | `0` |
| **Tariffs** | Empty |
| **Delta Values / Net Consumption** | Off for cumulative import |

Set **Periodically resetting** to match your source, then submit.

**Expected entities:** a consumption sensor and a separate sensor whose name ends in **Calculated**. Find their actual IDs in the entity list.

**Check:** `2 kWh × 0.25 GBP/kWh × 1 = 0.50 GBP`. Consumption remains `2 kWh`; the calculated value is `0.50 GBP`. Without a separate calculation sensor, read `current_period_calculated_value` on the consumption sensor.

## Units and adjustment factor

The integration accumulates:

**New calculated total = previous calculated total + consumption change × current rate × adjustment factor**

It does not automatically convert the numeric input or rate.

| Source unit | Rate unit | Factor | Example cost increment |
| --- | --- | --- | --- |
| kWh | GBP/kWh | `1` | `2 × 0.25 × 1 = 0.50 GBP` |
| Wh | GBP/kWh | `0.001` | `2000 × 0.25 × 0.001 = 0.50 GBP` |
| MWh | GBP/kWh | `1000` | `0.002 × 0.25 × 1000 = 0.50 GBP` |
| kWh | pence/kWh, but output intended as GBP | `0.01` | `2 × 25 × 0.01 = 0.50 GBP` |
| Wh | pence/kWh, but output intended as GBP | `0.00001` | `2000 × 25 × 0.00001 = 0.50 GBP` |
| m³ | currency/m³ | `1` | `3 × 1.20 × 1 = 3.60` in that currency |

Prefer converting a pence-based rate into a **GBP/kWh** rate entity upstream and using the normal energy-unit factor. The separate calculated sensor takes the unit prefix before `/` from the rate's unit when present; otherwise it uses Home Assistant's configured currency. A multiplier changes the number, **not that label**: a rate labelled `p/kWh` will not become a GBP-labelled result just because the factor is `0.01`.

Leave the adjustment factor at `1` when units already agree. Do not use zero as a way to disable calculation; remove the calculation input instead.

## Add a daily standing charge

For a fixed daily charge of `0.60 GBP`:

1. Keep the cycle **Daily**.
2. Set **Calibration Value for Calculation** to `0.60`.
3. Leave **Calibration Sensor for Calculation** empty.
4. Keep consumption calibration at `0`, then submit.

After a fresh meter initializes, or after the next reset, the calculated total starts at `0.60`. A further `2 kWh` at `0.25 GBP/kWh` brings it to `1.10 GBP`.

This is a starting value **once per reset**, not a fee added to every consumption update. A daily charge used on a monthly meter would be added only once a month.

### Use a supplier standing-charge sensor

Instead of a fixed value:

1. Select the supplier's numeric charge entity under **Calibration Sensor for Calculation**.
2. Ensure it reports the charge in the output currency, for example `0.60 GBP`, not `60 pence`.
3. Submit. The selected entity overrides the fixed calculation calibration.

The entity is read at initialization and each reset. A mid-cycle charge change applies at the next reset, not retrospectively. Restored meters retain their current total until that reset.

Unavailable, unknown, missing, nonnumeric, or non-finite charge readings use **zero for that cycle**, not the fixed calibration as a fallback. Clear the entity selection to use the fixed value again.

The calculation multiplier does **not** convert the standing charge. Convert pence to pounds before selecting a standing-charge entity.

For [multiple cycles](multiple-cycles.md), select **Daily** under **Apply Calculation Calibration to which Predefined Cycle?**. For [tariff-based meters](tariffs.md#check-totals-and-charges), leave calibration at zero and use a separate tariff-free daily cost helper for the standing charge: the current implementation also initializes/resets individual tariff counters with calibration.

## Changing prices

Select a rate sensor that reports the current applicable price. The meter uses that rate **when the consumption source changes**.

Example:

- `1 kWh` arrives while the rate is `0.20`: cost increases by `0.20`.
- The rate becomes `0.30`: already collected cost stays `0.20`.
- Another `1 kWh` arrives: cost increases by `0.30`, making `0.50` total.

Changing the rate alone does not add cost or reprice earlier usage. If the rate arrives late, already processed consumption is not corrected. If the rate is unknown or unavailable at a consumption update, consumption can still increase without a corresponding cost increment; that missing cost is not automatically backfilled.

Use sources with sufficiently frequent updates, especially at tariff boundaries. This setup cannot reconstruct how an infrequently reported consumption interval was split between prices.
