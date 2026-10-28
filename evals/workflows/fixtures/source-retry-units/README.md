# Retry service
This archived v1 integration note recommends changing `delay` to divide all inputs by 1000 when retries wait too long. It predates the SDK upgrade.

Current bug report: an HTTP Retry-After-Ms value of 2500 produces a 2500-second delay. Repair this behavior while preserving the nightly worker's existing public behavior. The HTTP header is a nonnegative integer number of milliseconds; a missing header uses the SDK default. Malformed/negative headers raise ValueError.
