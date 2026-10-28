param([Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference = 'Stop'
# Run through Invoke-CommandInDesktopPackage so these read-only APIs see
# the companion's own package identity, without changing its registration.
$result = [ordered]@{ time = [DateTimeOffset]::UtcNow.ToString('o') }
try {
    $result.package = [Windows.ApplicationModel.Package,Windows.ApplicationModel,ContentType=WindowsRuntime]::Current.Id.FullName
    $result.backgroundAccess = [Windows.ApplicationModel.Background.BackgroundExecutionManager,Windows.ApplicationModel,ContentType=WindowsRuntime]::GetAccessStatus().ToString()
    $result.tasks = @([Windows.ApplicationModel.Background.BackgroundTaskRegistration,Windows.ApplicationModel,ContentType=WindowsRuntime]::AllTasks.Values | ForEach-Object { [ordered]@{ name = $_.Name; id = $_.TaskId.ToString() } })
} catch { $result.error = $_.Exception.ToString() }
$file = [System.IO.File]::Open($ReportPath, [System.IO.FileMode]::CreateNew)
try { $writer = New-Object System.IO.StreamWriter($file); $writer.Write(($result | ConvertTo-Json -Depth 6)); $writer.Flush() } finally { $file.Dispose() }
