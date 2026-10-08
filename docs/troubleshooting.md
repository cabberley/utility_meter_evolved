# Troubleshooting and maintenance

[All guides](README.md) · [Common options](getting-started.md#common-options)

## Helper does not appear

- Confirm **Utility Meter Next Gen** is installed in HACS.
- Restart Home Assistant after installation or an update.
- Confirm your Home Assistant version meets the integration's [compatibility requirement](../README.md#compatibility).
- Look under **Settings → Devices & services → Helpers → Create helper**.
- Check **Settings → System → Logs** for integration loading errors.

## Source cannot be selected or meter does not increase

1. Inspect the source in **Developer tools → States**.
2. Check it is a supported consumption sensor with appropriate device class and a numeric state.
3. Use energy, not power; volume, not instantaneous flow.
4. Confirm the source actually changes. New meters do not import historical usage.
5. Check **Delta Values**: off for cumulative totals, on only for incremental reports.
6. For tariffs, verify the active selector value. `paused` is expected on inactive normal tariffs.
7. If the source dropped, Net Consumption off ignores negative adjustments. Only enable it for genuinely bidirectional readings.

Do not modify a live source's state in Developer tools to simulate consumption; a fake jump can contaminate your real meter. Use a separate test setup if you need controlled readings.

## Value is stale but still available

**Sensor always available** retains the last known value during source outages. Check the source's own availability and last update; a retained meter value does not mean collection is current.

For never-resetting sources, **Periodically resetting** off can bridge an unavailable interval using the last valid reading. Do not use this if a reboot could have reset the source counter.

## Consumption looks right but cost is wrong

| Symptom | Check |
| --- | --- |
| Cost is 1000 times too high/low | Wh/kWh/MWh conversion and adjustment factor |
| Cost is 100 times too high | Pence/cents versus pounds/dollars |
| Standing charge is too high | Charge entity must already be in output currency; the multiplier does not apply to calibration |
| Cost did not change when the rate changed | Costs update on consumption changes, not rate changes alone |
| Cost missed some usage | Rate availability and reporting timing; missing calculations are not backfilled |
| Wrong currency label | Rate unit prefix before `/`, or Home Assistant currency if there is no prefix |
| No separate cost entity | Enable **Create a separate Calculation Sensor**; otherwise inspect the consumption entity's calculated-value attributes |

A rate that changes late does not reprice already processed consumption. See [changing prices](costs.md#changing-prices).

For a separate calculated sensor that is unexpectedly unavailable, first check the linked consumption sensor and its `current_period_calculated_value`, then check the logs. The calculated entity exposes that attribute; it does not run an independent cost calculation.

## Standing charge is missing or repeated

- Use **Calculation** calibration, not consumption calibration.
- Use a Daily cycle for a once-per-day charge.
- For multiple cycles, select **Daily** as the calculation calibration target.
- For tariffs, keep calibration at zero: individual tariff meters currently receive it too. Use a separate tariff-free helper for standing charges; see the [tariff limitation](tariffs.md#check-totals-and-charges).
- An entity-backed calibration overrides the fixed value. Invalid readings use zero for that cycle.
- A restored meter keeps its current totals until the next reset; changing calibration is not an immediate reprice.
- Monthly/yearly meters do not inherit standing charges from daily meters.

## Reset time is wrong

- Check Home Assistant's time zone and the entity's `next_reset`.
- Check predefined offsets; **Offset** changes timing, not consumption.
- Use a five-field CRON expression with no seconds.
- For billing dates, prefer an explicit [CRON schedule](schedules.md).
- Remember that the first period is partial and daylight saving can affect elapsed cycle length.

## Options and entity changes

Open the helper's options from its Settings entry. Depending on the configuration type, you can change sources, rate inputs, cycles or CRON pattern, calibration, and calculation sensor creation.

- Tariffs must be introduced at creation. Edit their list later only on a tariff-based helper.
- To stop using a rate, use **Remove Input Calculation Sensor** when offered.
- Clearing a calibration entity selection returns that calibration to its fixed value.
- Configuration type is fixed; create a new helper to change between predefined, multiple, and CRON.
- Adding new cycles does not backfill history; removing cycles/tariffs can remove entities.
- Multiple-cycle helpers currently require at least two actual reset cycles. If reduced to one, restore a second cycle in options or create a single-predefined helper.
- Example entity IDs in these guides are placeholders. If you rename an ID, update external dashboard, script, and automation references and verify the linked calculated sensor afterward.

## Manual calibration and reset

These are different from recurring calibration options:

- In **Developer tools → Actions**, **Utility Meter Next Gen: Calibrate** (`utility_meter_next_gen.calibrate`) sets a consumption sensor's **current** value. It does not rewrite past history or recompute its accumulated cost.
- **Utility Meter Next Gen: Reset** (`utility_meter_next_gen.reset`) exposes a **select-entity** target for tariff-based meters. Resetting that selector resets its linked counters, including multiple cycles sharing it. Do not assume it targets a single cycle or accepts a tariff-free sensor.
- Scheduled resets restart consumption and calculation at their configured calibration values and retain previous-period values in attributes.

Record current totals before a manual change; it is not an undoable history edit. For a tariff-free meter, use its configured schedule rather than the select-targeted reset action.

## Reporting a problem

Include the Home Assistant/integration versions, configuration type, cycle or CRON pattern, option values, source units and relevant state changes, expected result, actual result, and relevant log lines.

If sharing a screenshot of **Developer tools → States** or the helper options, crop/redact personal names, locations, account details, private addresses, and any credentials first.
