# AF-05 fixture (PHASE-DEFERRED): binning destroys arrival signal

Active check deferred to Phase 3+ — the hook greps inside analysis/src/ for
daily/hourly `resample()` calls, but analysis/src/ does not exist yet.

When Phase 3+ adds analysis/src/, violating fixture: a synthetic .py file calling
`df.resample('D')` or `df.resample('1h')`.
