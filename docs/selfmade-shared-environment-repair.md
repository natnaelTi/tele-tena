# Separate shared-environment repair proposal —14October2026

**Not applied. Not part of the TeleTena package update.** The update must stop until
this baseline is coherent. Do not use `--no-deps`, relax update constraints, run
`bench update`, change Frappe/ERPNext versions, reset source or discard yarn.lock.

## Observed facts

The supplied transcript reports44 apps in `sites/apps.txt`, not just the3 installed
on TeleTena's site. Frappe16.2.1 commit8f6e247, ERPNext16.1.0 commitbb2bada,
Python3.14.2, Node24.13.0, MariaDB10.6.22, Redis6.0.16. All3 queues subscribed;
scheduler enabled/unpaused. Subsequent failed attempt stopped shared web/workers/
scheduler and changed TeleTena code only. The current running state must be checked.

Eight pip-check messages concern6 dependency names:

| Dependency | Reported baseline | Constraints observed | Proposed minimum investigation |
|---|---|---|---|
| Click |8.3.1 |Frappe `~=8.3.1`; Bench5.29.0 `~=8.2.0` |**Disjoint.** Retain Frappe's compatible Click; isolate Bench CLI in its own environment. First identify launchers/service commands and any app requiring Bench as a library. |
| Requests |2.33.1 |Frappe and Bench `~=2.32.5` |2.32.5 is a tested candidate only if every other app's source/metadata requirements allow it. |
| Cryptography |48.0.0 |Frappe `~=46.0.3`; pyOpenSSL25.3.0 `>=45.0.7,<47` |Intersection46.0.3–<46.1. Tested candidate46.0.7; check other apps first. |
| OAuthlib |3.3.1 |Frappe `~=3.2.2` |Tested candidate3.2.2, subject to all-app requirements. |
| Websockets |16.0 |Frappe `~=15.0.1` |Tested candidate15.0.1, subject to all-app requirements and consumers. |
| urllib3 |2.6.3 |botocore1.31.85 `>=1.25.4,<2.1` |Do **not** blindly downgrade urllib3. Identify boto3/botocore consumers and their pins; assess a compatible SDK pair or isolate that legacy integration. No pair is prescribed without its owning apps' requirements. |

Requirements come from the transcript and the exact pinned Frappe source/installed
metadata, not a guessed latest version. ERPNext16.1.0's declared dependencies were
also inspected locally. Local healthy Frappe16 used Click8.3.3, Requests2.32.5,
Cryptography46.0.7, OAuthlib3.2.2, Websockets15.0.1, urllib32.8.0 and pyOpenSSL25.3.0.
**That is compatibility evidence for the tested apps, not permission to install
these pins into the44-app server.** Botocore/boto3 were absent locally.

## Required read-only observations

Run as smcs, not root. These tools come from the corrected release; fetching does
not switch code or change data. Store output privately, never paste configuration,
provider keys, credentials, full pip URLs or environment variables into chat.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
REPAIR_RELEASE=800a591ac6af9c6c3b4afd61ed4353be4ff0826e
git -C apps/tele_tena fetch origin feat/mvp-release-handover
AUDIT=$(mktemp -d /home/smcs/teletena-dependency-audit.XXXXXXXX)
for TOOL in dependency_checkpoint.py shared_dependency_audit.py check_frappe_lock.py; do
  git -C apps/tele_tena show "$REPAIR_RELEASE:scripts/$TOOL" > "$AUDIT/$TOOL"
done
env/bin/python "$AUDIT/shared_dependency_audit.py" --bench /home/smcs/frappe-bench > "$AUDIT/all-app-requirements.json"
env/bin/python "$AUDIT/check_frappe_lock.py" apps/frappe
git -C apps/frappe diff HEAD --binary -- yarn.lock > "$AUDIT/frappe-yarn-lock.patch"
cp apps/frappe/yarn.lock "$AUDIT/frappe-yarn.lock"
cp sites/apps.txt "$AUDIT/apps.txt"
command -v bench
# If this is a file, inspect its shebang; do not print shell aliases with secrets.
head -1 "$(command -v bench)"
env/bin/python -m pip show frappe-bench boto3 botocore pyOpenSSL
sudo supervisorctl status
```

Supply the audit's `focused_requirement_edges`, `all_active_conflicts`,
`missing_bench_app_metadata`, `unresolved_source_inputs`, relevant owning-app
requirements and CLI executable/shebang. The audit reads every installed
package's active requirements AND every Bench app's declarative source files;
it does not execute arbitrary setup.py. Resolve nested/dynamic requirements,
package-name aliases, private/direct-source provenance and deployed optional
extras explicitly. Missing metadata is not a positive compatibility result.

Also identify the executable paths used by the confirmed Supervisor web/workers/
scheduler; inspect the existing protected configuration locally. Do not publish
its environment entries. We need to know whether any service invokes an
app-env `bench` launcher before removing that distribution. No service configuration
change is assumed or authorized by this proposal.

## Minimal staged plan, after observations

1. Preserve private package/version/editable-identity snapshots, app commits,
   lockfile+patch, service/launcher metadata, matched database/public/private/config
   backups and original package artifacts. Do not change the server yet.
2. Build a **separate CLI environment** with the same Python and Bench5.29.0.
   Normal pip resolution installs its own Click8.2.x/Requests2.32.5 there. Validate
   CLI pip-check and Bench commands against a cloned compatible staging bench.
   Do not blindly upgrade Bench. Only after launcher/dependent-app review, arrange
   the stable CLI path and remove the conflicting Bench distribution from the
   application env. If an app requires Bench as a runtime library, stop: isolation
   needs a different, reviewed solution. Removing it first could break workers.
3. Compute allowed intersections from **all44 apps and installed distributions**.
   If allowed, trial only the4 candidate replacements (Requests/Cryptography/
   OAuthlib/Websockets) above in staging. Retain Click's working version. Preserve
   every other version and editable identity. Account for any explicitly necessary
   transitive change; do not allow a resolver to replace unrelated packages.
4. Resolve urllib3/boto3/botocore as a separate owning-app decision. Preserve a
   matched SDK pair and prove its consumer works. If an old exact pin makes a
   coherent shared env impossible, propose a separate integration/bench rather
   than weakening Frappe or silently downgrading shared packages.
5. Generate and review a normal pip dry-run report in staging against all root
   requirements and protected constraints. Reject incompatible/unrelated changes.
   Execute only the reviewed plan in staging. Require zero pip-check conflicts,
   original editable application identities and relevant smoke/SDK/TLS workflows.
6. Schedule an explicit shared-bench maintenance window only after those checks.
   Apply the separately reviewed repair with a rollback environment available;
   restore exact identified launcher/service paths. Recheck all-app requirements,
   pip-check and queues. Then take a **new** healthy dependency snapshot for the
   TeleTena update. Never reuse the original conflicted snapshot as if repaired.

The TeleTena update guard deliberately cannot authorize this repair: it permits
only TeleTena replacement. Separate repair evidence and authorization are required.
No ready-to-run package downgrade command is supplied while44-app compatibility
and the boto consumer remain unknown.

## Lockfile decision and compatibility evidence

The supplied diff changes only caniuse-lite1.0.30001564 →1.0.30001765, its registry
URL and integrity. Preserve it as a deliberate Browserslist data update. The
read-only `check_frappe_lock.py` compares the entire working file to exactly that
replacement at the known Frappe commit and rejects anything else. It does not
modify framework source, clear Git changes or claim that all shared frontend
builds have been verified. The update records/backups its bytes and verifies they
remain unchanged after asset build.

Locally tested: initial install and guarded existing TeleTena upgrade; healthy
Frappe/ERPNext16 pip-check; isolated Bench5.29.0 CLI pip-check and site list-apps;
10 guard/archive/lock regressions on Python3.12 and3.14.2. Original26-table
operational rows, owner balances and credentials survived migration/repeat/seed.
This supports the **strategy**, not a claim that the remote44-app repair passed.
