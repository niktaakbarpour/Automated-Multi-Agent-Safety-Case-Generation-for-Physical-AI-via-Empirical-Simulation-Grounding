# Temporal validity contract

Saved indices and endpoint clocks are verified for the four fixed development runs. Frame 0 is before settling; frames 1–10 are the ten settling endpoints; frame 10 anchors pre-first-policy assessment. Policy step i ends at frame i+11. Requested boundaries never move to a convenient observation. Setup context remains available through the terminal snapshot.

## Observations

All 1,312 saved frames are ordered and monotonic with no missing indices in the verified source projection. Observed simulator intervals span 0.04999999999997229–0.0500000000000167s, consistent with the nominal 20 Hz control configuration at floating-point precision. These extrema are observed values, not an alignment tolerance. Host recording intervals span about 0.02755–0.70561s; host time includes recording/inference overhead and is not a substitute simulator clock.

The model physics timestep is 0.002s. Across noninitial free-object samples, qpos(endpoint)-body_cache-h*qvel(endpoint) has maximum absolute translation residual 1.1015494072452725e-16m. This strengthens the existing last-forward-cache hypothesis for this Euler/model/recorder scope. It does not supply a calibrated temporal bound or producer-binary attestation.

The prior raw-position two-substep expression has maximum residual 3.6886336982067114e-7m over the full development sample, extending the narrower earlier targeted study. It remains a fit residual, not a camera timestamp or time-error bound. Do not divide it by velocity, convert it to a universal alignment window, or blend raw observables with native caches as simultaneous.

## Required temporal contract

Keep endpoint qpos/qvel/flattened state, native body/geom/contact caches, raw observables and camera exposures as separate bundles. Every derived quantity references its source indices, clock and phase uncertainty. Exact phase bounds remain null where unvalidated. Record observation brackets and censoring; do not invent onset times. Boundary-straddling or terminal-incomplete transitions remain unresolved.

Original cameras are sampled observables recorded in snapshot dictionaries. Independent exposure timestamps and historical observable/cache implementation binding remain insufficient for exact alignment. Twenty-four selected arrays were extracted to three Hestia sheets with raw-byte/source hashes. No visual review occurred, and no exposure bound is inferred from their labels. Nominal FPS is producer configuration, not a freshly audited MP4 timing measurement; MP4s were not restored.

Saved-state availability does not establish physics-substep or continuous coverage. No missing, unreviewed or unqualified transition is bridged into a negative. Static empirical joins need admitted compatible certificates; dynamic/handling/replacement composition remains unsupported. An optional missing camera cannot block an otherwise independently justified state witness, but every necessary timing dependency must be validated before empirical admission.
