# Reset schedules and CRON

[All guides](README.md) · [Multiple cycles](multiple-cycles.md)

## Choose the schedule type

| Need | Configuration type |
| --- | --- |
| One calendar-based meter | Create using a Predefined reset cycle |
| Several calendar-based meters | Create Multiple Predefined reset cycle Meters |
| Billing date or an explicit custom reset time | Create using a custom CRON pattern |

Predefined intervals include 5/10/15/20/30 minutes, hourly, daily, weekly, monthly, every two months, quarterly, half-yearly, and yearly. Single predefined setup also offers **No cycle** when you do not want automatic resets.

Daily/monthly/yearly meters with zero offset reset at local midnight, on the first of the month, and on January 1 respectively. Weekly with zero day offset uses Sunday. Inspect `next_reset` to confirm the schedule you actually configured.

## Monthly billing on the 15th

**Goal:** collect one billing period from midnight on the 15th until the next reset.

1. Create a **Utility Meter Next Gen** helper named `Billing electricity`.
2. Select your cumulative energy source and optional rate input.
3. Choose **Create using a custom CRON pattern** and submit.
4. Enter `0 0 15 * *` in the CRON field.
5. Configure the [common options](getting-started.md#common-options); leave tariffs empty unless needed.
6. Submit and check `next_reset` in **Developer tools → States**.

If created on the 20th, the first period starts on the 20th, not the previous 15th. The first reset ends that partial period. Later periods align to the billing date.

## CRON format

Use **five fields**, separated by spaces:

```text
minute hour day-of-month month day-of-week
```

`*` means every allowed value; `*/15` means every 15 within that field. Do not add a seconds field.

| Reset requirement | Pattern |
| --- | --- |
| Every 15 minutes, aligned to the hour | `*/15 * * * *` |
| Every day at 06:00 | `0 6 * * *` |
| Every Monday at 00:00 | `0 0 * * 1` |
| First day of each month at 00:00 | `0 0 1 * *` |
| 15th of each month at 00:00 | `0 0 15 * *` |
| First day of January, April, July, and October | `0 0 1 1,4,7,10 *` |

Prefer a wildcard for one of day-of-month/day-of-week unless you specifically need CRON's interaction between those fields. A pattern for day 31 skips months that have no 31st; it does not mean “the last day of every month.”

## Local time, offsets, and daylight saving

- Scheduling uses Home Assistant's configured time zone, not necessarily UTC.
- CRON defines calendar times, not fixed elapsed durations. Local-time schedules around daylight-saving transitions can have different elapsed cycle lengths; check `next_reset` and test your chosen boundary.
- Single predefined **Offset** affects schedule timing; it does not set a starting sensor value. Seconds are ignored.
- Multiple predefined cycles do not support offsets.
- For a particular monthly billing day, enter an explicit CRON pattern rather than relying on the predefined offset's day field.

## Verify a reset

1. Check the entity's `next_reset` before the boundary.
2. After the boundary, confirm `last_period` contains the previous consumption.
3. Confirm the current value has restarted at its configured consumption calibration (usually zero).
4. If using costs, check `last_period_calculated_value` and the new `current_period_calculated_value`.

You can choose a short interval on a **temporary test helper** to observe this without disrupting an existing billing meter. Do not manually reset a production meter merely to test its schedule.

## Edit a schedule

Open the helper's options to change its existing predefined cycle or CRON pattern. Configuration types remain fixed: to move between single predefined, CRON, and multiple predefined setups, create a new helper.

Changing a schedule does not backfill or redistribute history. Check the next reset and the current partial period after reconfiguration.
