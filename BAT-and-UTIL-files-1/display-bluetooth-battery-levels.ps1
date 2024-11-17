Get-PnpDevice -Class 'Bluetooth' | ForEach-Object {
    $local:test = $_ |
    Get-PnpDeviceProperty -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' |
        Where Type -ne Empty;
    if ($test) {
        "Battery percentage of $($_.FriendlyName) is: ";
        Get-PnpDeviceProperty -InstanceId $($test.InstanceId) -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' | % Data
    }
}
