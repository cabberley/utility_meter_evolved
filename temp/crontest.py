#crontest
from cronsim import CronSim, CronSimError
from datetime import datetime
import voluptuous as vol


def validate_cron_pattern(pattern):
    """Check that the pattern is well-formed."""
    try:
        CronSim(pattern, datetime(2020, 1, 1))  # any date will do
    except CronSimError as err:
        #_LOGGER.error("Invalid cron pattern %s: %s", pattern, err)
        raise vol.Invalid("Invalid pattern") from err
    return True


pattern = "0 0 * * a"
try:
    validate_cron_pattern(pattern)
    print(f"Pattern '{pattern}' is valid.")
except vol.Invalid as e:
    print(f"Pattern '{pattern}' is invalid: {e}")
