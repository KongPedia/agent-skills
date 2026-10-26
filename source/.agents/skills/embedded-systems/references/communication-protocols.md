# Communication Protocols

## Target compatibility and authority

Read the [target boundary and SDK references](../SKILL.md#target-compatibility-and-authority) first.
Use the selected MCU/SDK version and existing product transport, not registers or interrupt recipes from another target.
The checks below describe design/review requirements, not tested drivers or permission to access hardware.
Do not change dependencies, flags, watchdogs or firmware configuration from this guide.

## I2C Master Implementation

- Confirm the board's pins, pull-ups, voltage, address convention and bus timing before changing the owner driver.
- Use the installed SDK's transaction API. Check status, transferred length and timeout; preserve repeated-start
  requirements for register reads instead of assuming separate write/read transactions are equivalent.
- Define bounded recovery for NACK, arbitration loss and a stuck bus. A timeout must release transaction resources;
  it does not establish that the peripheral saw no write.

## SPI Master Implementation

- Match clock polarity/phase, word size, bit order, chip-select lifetime and speed to the actual peripheral.
- Validate buffer lengths and lifetimes before submission. Keep DMA buffers owned until completion or confirmed abort;
  check the installed driver's alignment and memory-capability requirements.
- Bound each wait and handle completion, timeout and transfer errors separately. Do not reuse a decremented unsigned
  loop counter across waits, or treat an enable bit clearing as proof of successful DMA completion.
- Use the existing driver to release chip select and recover after failure; do not transplant register-level DMA setup.

## UART with Interrupt and Circular Buffer

- Reuse the existing product UART/USB transport and SDK driver. Keep ISR work bounded and use the matching ISR-safe APIs.
- Define full/empty behavior, capacity and overflow reporting before using a ring buffer. `volatile` is not cross-core
  synchronization; single-owner foreground queues are not automatically safe for ISR/task or multicore access.
- Preserve parser length/CRC rejection, resynchronization and bounded per-tick work. Keep binary application streams
  free of debug/provisioning text when their protocol requires it.
- Inspect the existing bounded transport queue before adding another. Preserve admission failure, pending-byte and
  partial-consumption semantics. A foreground single-owner queue is not a generic synchronized ISR queue.

## CAN Bus Implementation

- Confirm the selected MCU, installed driver, external transceiver, termination, bitrate and identifier/frame mode.
  Do not assume another chip's mailbox layout or that every variant supports the same peripheral.
- Validate identifiers, frame flags and payload length before indexing/copying. Read only the caller-provided bytes;
  a short payload does not permit an unconditional eight-byte read. Handle remote frames according to the driver API.
- Check queue admission and actual transmit/error events separately. Bound retries and handle bus-off without replaying
  stale actuator commands; accepted/queued is not physical execution.

## Best Practices

- Keep one transaction/buffer owner and explicit timeout, overflow and recovery policies.
- Use the existing parser/transport and offline production-code seams before adding a new driver or parser.
- Preserve the product's local safety priority and protocol lease/deadline expiry under saturation, including reconnect work.
- Builds, offline checks and ACKs do not prove electrical timing or physical success. Live serial/bus access needs the
  repository's separate target-specific authorization; reset/open can itself trigger outputs.
