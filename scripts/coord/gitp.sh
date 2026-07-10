#!/usr/bin/env bash
# scripts/coord/gitp.sh — canonical push for the octanex-mcp coordination loop.
#
# Usage: bash scripts/coord/gitp.sh ["commit message"]   (stages nothing; expects
#        a clean commit ready, OR pass a message to commit all tracked changes)
#
# Does: git push origin main, then notifies the peer instance instantly via
# coord/notify.sh (SSH fast-path + local outbox). Deterministic alternative to
# relying on git's post-receive hook (which does not fire through some git paths).
#
# Non-fatal: a notify failure never breaks the push.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO" || { echo "gitp: cannot cd to repo"; exit 1; }

MSG="${1:-}"
if [ -n "$MSG" ]; then
  # commit all currently-staged + tracked-modified; leave untracked scratch alone
  git add -u
  git commit -q -m "$MSG" || { echo "gitp: commit failed (nothing to commit?)"; exit 1; }
fi

# push (use the range we are about to push for an accurate notify)
OLD="$(git rev-parse origin/main 2>/dev/null)"
git push origin main 2>&1 | tail -4 || { echo "gitp: push failed"; exit 1; }
NEW="$(git rev-parse HEAD 2>/dev/null)"

# notify peer with the real range
if [ "$OLD" != "$NEW" ]; then
  bash "$SCRIPT_DIR/notify.sh" --from "$OLD" --to "$NEW" --verified || true
  echo "gitp: pushed + notified peer ($OLD..$NEW)"
else
  echo "gitp: already up to date (nothing pushed)"
fi
