# Sensor-time audit

Inspected all 58075 saved snapshots and 53323 action labels across 432 executions / 104 variants. Checked 464600 raw sensor groups for explicit timestamp/clock attributes and datasets. No explicit per-sensor timestamp fields were found. This does not prove an arbitrary undocumented array cannot encode time; such an interpretation remains unsupported.

Recorded simulator endpoint labels are distinct from frame index. Frame host UTC, POSIX-API wall nanoseconds and monotonic nanoseconds are recorded at recorder calls, not calibrated sensor exposure times. Actions have post-call simulator/host labels; policy and inference records carry UTC labels and elapsed durations. CLOCK_AUDIT.json preserves original values and selectors. i_clock_labels stores original labels, without interpolation or invented samples.

Primary evidence: source_evidence/recording_base.py, hash-matched to execution metadata (PRODUCER_EVIDENCE.json). Lines 11, 52, 78, 129, 135 and 167 show datetime.now, time.time_ns, time.monotonic_ns, performance durations and post-action labels. Simulator serialization is source-bound by Phase 5H primary-source traceability and retested by unchanged source-value benchmarks. Present-day CPython semantics do not attest the original running binary.

The established 0.05-second saved interval and 0.002-second physics step remain scoped to admitted recordings and version-bound XML/model validation. The -0.002-second cache interpretation is CONDITIONAL. No per-sensor instant, exposure alignment, drift model, calibrated wall-clock origin or host-to-simulator affine mapping is asserted. Observed wall-minus-monotonic spans are descriptive, not synchronization parameters.

Seconds queries filter actual recorded simulator labels inclusively. They do not manufacture sensor timestamps from frame index. Same-index association, endpoint simulator time and physical simultaneity remain distinct. Missing sensor clocks and resource payloads are explicit in CLOCK_DOMAIN_REGISTRY.csv.
