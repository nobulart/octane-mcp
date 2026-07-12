(*
 * octane_flush_queue.applescript
 * ------------------------------------------------------------------
 * Move (NEVER delete) all queued command files from the Octane MCP workspace
 * queue/ into a dated backup directory. Recoverable. Returns a count.
 *
 * The container queue/ is shared and persistent across sessions/agents, so
 * prior sessions can leave stale commands that would otherwise re-render on
 * the next drain. Run this before a live render.
 *
 * RUN:
 *   osascript scripts/octane_flush_queue.applescript
 *)
set wsRoot to (system attribute "HOME") & "/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
set qDir to wsRoot & "/queue"
set stamp to do shell script "date +%Y%m%dT%H%M%S"
set backupDir to wsRoot & "/queue_backup/" & stamp

set cleared to do shell script "
if [ -d " & quoted form of qDir & " ]; then
  n=$(ls -1 " & quoted form of qDir & "/*.json 2>/dev/null | wc -l | tr -d ' ');
  if [ \"$n\" -gt 0 ]; then
    mkdir -p " & quoted form of backupDir & ";
    mv " & quoted form of qDir & "/*.json " & quoted form of backupDir & "/;
  fi;
  echo \"$n\";
else
  echo 0;
fi"
return "flushed " & cleared & " stale queue file(s) -> " & backupDir
