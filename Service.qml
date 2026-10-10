import QtQuick
import Quickshell.Io

Item {
  id: root

  function sync() {
    if (!syncProcess.running) syncProcess.running = true
  }

  Process {
    id: syncProcess
    command: ["python3", Qt.resolvedUrl("sync-theme.py").toString().replace(/^file:\/\//, "")]
    stderr: StdioCollector {
      onStreamFinished: if (text.trim()) console.warn("System Monitor Theme Sync: " + text.trim())
    }
  }

  // Also repairs settings saved by either app when it exits.
  Timer {
    interval: 3000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.sync()
  }

  IpcHandler {
    target: "system-monitor-theme"
    function sync(): void { root.sync() }
  }
}
