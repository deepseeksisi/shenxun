# Messenger agent v4: TopMost borderless overlay (ASCII only!)
$dir = "C:\Users\Public\shenxun-say"
$msgFile = Join-Path $dir "msg.txt"
$stampFile = Join-Path $dir "stamp.txt"
$logFile = Join-Path $dir "agent.log"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$code = @"
using System.Windows.Forms;
public class OverlayForm : Form {
  protected override bool ShowWithoutActivation { get { return true; } }
  protected override CreateParams CreateParams {
    get { var cp = base.CreateParams; cp.ExStyle |= 0x08000000; return cp; }
  }
}
"@
try { Add-Type -TypeDefinition $code -ReferencedAssemblies System.Windows.Forms, System.Drawing } catch {}

function Show-Overlay([string]$text) {
  $f = New-Object OverlayForm
  $f.FormBorderStyle = 'None'
  $f.StartPosition = 'Manual'
  $f.TopMost = $true
  $f.ShowInTaskbar = $false
  $f.BackColor = [System.Drawing.Color]::FromArgb(20, 22, 28)
  $f.Opacity = 0.9
  $lbl = New-Object System.Windows.Forms.Label
  $lbl.Text = $text
  $lbl.ForeColor = [System.Drawing.Color]::FromArgb(245, 240, 230)
  $lbl.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 14)
  $lbl.AutoSize = $true
  $lbl.MaximumSize = New-Object System.Drawing.Size(800, 0)
  $lbl.Padding = New-Object System.Windows.Forms.Padding(20, 14, 20, 14)
  $f.Controls.Add($lbl)
  $sz = $lbl.PreferredSize
  $f.ClientSize = New-Object System.Drawing.Size($sz.Width, $sz.Height)
  $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
  $f.Left = [int](($wa.Width - $f.Width) / 2)
  $f.Top = [int]($wa.Height * 0.13)
  "bounds left=$($f.Left) top=$($f.Top) w=$($f.Width) h=$($f.Height)" |
    Out-File -FilePath $logFile -Append -Encoding UTF8
  $timer = New-Object System.Windows.Forms.Timer
  $timer.Interval = 9000
  $timer.Add_Tick({ $timer.Stop(); $f.Close() })
  $timer.Start()
  $f.Show()
  $f.TopMost = $true
  while ($f.Visible) { [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 50 }
}

"agent4 start $(Get-Date -Format s) session=$((Get-Process -Id $PID).SessionId)" |
  Out-File -FilePath $logFile -Append -Encoding UTF8

while ($true) {
  try {
    if (Test-Path $msgFile) {
      $stamp = (Get-Item $msgFile).LastWriteTimeUtc.Ticks
      $last = 0
      if (Test-Path $stampFile) { $last = [int64](Get-Content -Raw $stampFile) }
      if ($stamp -gt $last) {
        Set-Content -Path $stampFile -Value $stamp -Encoding ASCII
        $msg = (Get-Content -Raw -Encoding UTF8 $msgFile).Trim()
        if ($msg.Length -gt 0) {
          "show4 $(Get-Date -Format s)" | Out-File -FilePath $logFile -Append -Encoding UTF8
          Show-Overlay $msg
        }
      }
    }
  } catch {
    "ERR $($_.Exception.Message)" | Out-File -FilePath $logFile -Append -Encoding UTF8
  }
  Start-Sleep -Seconds 2
}
