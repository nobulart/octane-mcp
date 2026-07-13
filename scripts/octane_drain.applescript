(*
 * octane_drain.applescript [TIMEOUT_S] [PREVIEW_PATH]
 * ------------------------------------------------------------------
 * Click Octane X > Script > hermes_bridge_oneshot.generated (ONE click drains
 * the WHOLE queue) and then poll until the workspace queue/ is empty AND the
 * preview PNG is freshly written (newer than the click), or TIMEOUT_S elapses.
 * Prints a JSON summary:
 *   { "clicked", "queue_remaining", "preview_written", "waited", "ok" }
 *
 * LOCK-AWARE (shared-engine scheduler): before draining, this script reads
 *   ROOT/render.lock  and refuses to drive the engine unless IT owns a live
 *   (non-stale) lease for the job it is about to render. Without this guard a
 *   hand-rolled drain could double-drive Octane behind another agent's back
 *   (the exact failure the filesystem scheduler exists to prevent). To set the
 *   lock, run the Python dispatcher (octanex_mcp.scheduler.dispatch_and_drain)
 *   — or, for a manual single-agent override, delete ROOT/render.lock first.
 *   If a live lock is held by someone else, this script exits 2 (busy).
 *
 * On success it also writes  ROOT/jobs/<job_id>/done.json  (when a job_id is
 * resolvable from the lock) so completion is filesystem-observable even if the
 * controlling process is SIGTERM'd mid-render.
 *
 * Exit codes:
 *   0  always returns JSON (inspect the "ok" field for drain success)
 *   2  engine busy — a live lock is held by another agent (do not drain)
 *   non-zero (other)  only on a HARD control failure (click not found / TCC / app down)
 *
 * The persistent bridge's auto-poll timer is BROKEN (timer create attempt 1
 * failed), so prefer this one-shot drain. After clicking, do NOT re-click
 * while the queue is empty — a second click while save_preview is rendering is
 * ignored and would kill that render.
 *
 * RUN:
 *   osascript scripts/octane_drain.applescript
 *   osascript scripts/octane_drain.applescript 120 /abs/path/preview.png
 *
 * NOTE: Octane X must already be running + UI-ready (launch with
 * octane_launch.applescript first), OR use octane_relaunch_drain.applescript
 * which launches + drains in one shot.
 *)
on run argv
  set wsRoot to (system attribute "HOME") & "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
  set qDir to wsRoot & "/queue"
  set lockPath to wsRoot & "/render.lock"
  set timeoutS to 90
  set previewPath to wsRoot & "/renders/preview.png"
  if (count of argv) > 0 then
    try
      set timeoutS to (argv's item 1 as number)
    end try
  end if
  if (count of argv) > 1 then
    set previewPath to argv's item 2 as text
  end if

  -- 0) Lock guard: refuse to drive the engine unless WE own a live lease.
  set lockState to (do shell script "test -f " & quoted form of lockPath & " && cat " & quoted form of lockPath & " || echo ''")
  if lockState is not "" then
    set isStale to (do shell script "python3 -c \"import json,sys,time; d=json.loads(open(" & quoted form of lockPath & ").read()); print('1' if time.time()>=float(d.get('expires_at',0)) else '0')\" 2>/dev/null || echo 1")
    if isStale is "0" then
      -- A live lock is held. Only proceed if it is ours (same owner_agent_id);
      -- for a hand-rolled drain we cannot know our id, so treat any live lock
      -- held by another process as busy and refuse.
      set holder to (do shell script "python3 -c \"import json,sys; d=json.loads(open(" & quoted form of lockPath & ").read()); print(d.get('owner_agent_id',''))\" 2>/dev/null || echo ''")
      set myId to (do shell script "python3 -c \"import os,json; print(os.environ.get('OCTANEX_AGENT_ID',''))\" 2>/dev/null || echo ''")
      if holder is not "" and holder is not myId then
        set out to "{\"clicked\":\"none\",\"queue_remaining\":-1,\"preview_written\":0,\"waited\":0,\"ok\":false,\"busy\":true,\"owner_agent_id\":\"" & holder & "\"}"
        return out
      end if
    end if
  end if

  set appName to "Octane X"
  set target to "hermes_bridge_oneshot.generated"
  set clickedName to ""

  -- 1) Click the one-shot bridge from the Scripts menu.
  tell application "System Events"
    if not (exists process appName) then
      error "Octane X not running — launch it first (octane_launch.applescript)."
    end if
    tell process appName
      set frontmost to true
      set menuCandidates to {"Script", "Scripts", "Lua", "File"}
      repeat with menuTitle in menuCandidates
        try
          set candidateMenu to menu 1 of menu bar item (menuTitle as text) of menu bar 1
          repeat with directItem in menu items of candidateMenu
            set itemName to name of directItem
            if itemName contains target then
              click directItem
              set clickedName to itemName
              exit repeat
            end if
          end repeat
          if clickedName is not "" then exit repeat
          repeat with submenuItem in menu items of candidateMenu
            try
              repeat with nestedItem in menu items of menu 1 of submenuItem
                set nestedName to name of nestedItem
                if nestedName contains target then
                  click nestedItem
                  set clickedName to nestedName
                  exit repeat
                end if
              end repeat
            end try
            if clickedName is not "" then exit repeat
          end repeat
        end try
        if clickedName is not "" then exit repeat
      end repeat
      if clickedName is "" then
        error "Could not find '" & target & "' in Octane X Scripts menu."
      end if
    end tell
  end tell

  -- 2) Snapshot the preview mtime BEFORE the drain so we can detect a fresh save.
  set beforeEpoch to 0
  set pngPreExists to (do shell script "test -f " & quoted form of previewPath & " && echo 1 || echo 0") as number
  if pngPreExists is 1 then
    set beforeEpoch to (do shell script "stat -f %m " & quoted form of previewPath) as number
  end if

  -- 3) Poll: queue empty + preview freshly written.
  set qRem to 9999
  set fresh to 0
  set waited to 0
  repeat while waited < timeoutS
    set qRem to (do shell script "ls -1 " & quoted form of qDir & "/*.json 2>/dev/null | wc -l | tr -d ' '") as number
    set fresh to 0
    set pngExists to (do shell script "test -f " & quoted form of previewPath & " && echo 1 || echo 0") as number
    if pngExists is 1 then
      set now to (do shell script "stat -f %m " & quoted form of previewPath) as number
      if now > beforeEpoch then set fresh to 1
    end if
    if qRem is 0 and fresh is 1 then exit repeat
    delay 2
    set waited to waited + 2
  end repeat

  set ok to (qRem is 0) and (fresh is 1)

  -- 4) On success, write jobs/<job_id>/done.json so completion is observable
  --    even if this process is SIGTERM'd right after. job_id comes from the lock.
  if ok then
    try
      set jobId to (do shell script "python3 -c \"import json; d=json.loads(open(" & quoted form of lockPath & ").read()); print(d.get('owner_job_id',''))\" 2>/dev/null || echo ''")
      if jobId is not "" then
        set doneDir to wsRoot & "/jobs/" & jobId
        do shell script "mkdir -p " & quoted form of doneDir
        set donePath to doneDir & "/done.json"
        set epoch to (do shell script "date -u +%Y-%m-%dT%H:%M:%SZ")
        set doneJson to "{\"schema_version\":\"1.0\",\"job_id\":\"" & jobId & "\",\"completed_at\":\"" & epoch & "\",\"outputs\":[\"" & previewPath & "\"],\"error\":null,\"ok\":true}"
        do shell script "printf '%s' " & quoted form of doneJson & " > " & quoted form of donePath
      end if
    end try
  end if

  set out to "{"
  set out to out & "\"clicked\":\"" & clickedName & "\","
  set out to out & "\"queue_remaining\":" & qRem & ","
  set out to out & "\"preview_written\":" & fresh & ","
  set out to out & "\"waited\":" & waited & ","
  set out to out & "\"ok\":" & (ok as text)
  set out to out & "}"
  return out
end run
