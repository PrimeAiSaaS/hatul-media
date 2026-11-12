# Trigger stubs (from 12.11)

Every scheduled task's prompt is now a short stub: role, permissions, hard limits, and "read agents/<agent>.md from the HQ artifact and follow it".
The full instructions live in HQ (https://claude.ai/artifact/LTd1as8v4rzTnxCN6bj6sJ, files agents/*.md) and are mirrored here as agents/full/<agent>_vN.md.

To change an agent's behaviour: edit the next _vN file here, publish it to HQ as agents/<agent>.md (publish_files, patch mode), update meta.json. No update_trigger needed.
update_trigger is needed only when a stub's permissions/limits change.

Pending (needs Gabi's approval in a session linked to his computer "מחשבסיתי"):
- voices (trig_01Qd9hKGPHxRCfWEfUr8aNr3): still runs the old voices_v3 text, whose push fails with 403. The stub below fixes it.
