# Connected patient profile/booking comparison

Built source: `d82948a3d5cc27e098370cce572da4d71d4904b4`.
Invited-review password access, actual patient Home/discovery, second distinct
published offering preview/focus return, full profile retains that offering after
reload, generated calendar/selected hover, disclosure preview/review/Back at
390/768/1440 passed. No booking submission or financial write in this read-only
journey. result.json is functional evidence; images require visual comparison.

Before fix, the same second-offering profile handoff failed on sourcebf3d63c at
390: the full profile defaulted to the first published service. Selected public
offering context is now passed in router state; stale/not-permitted offerings
still fall back only to services returned by the authoritative profile API.

Another earlier run defaulted to the first couples offering while asserting the
individual disclosure-review layout. Its test fixture selection was corrected
explicitly to follow the selected individual offering, without weakening either
couples consent policy or the individual disclosure assertion.
