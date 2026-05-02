$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.SendTimeout = 5000
$tcp.ReceiveTimeout = 5000
try {
    $tcp.Connect("161.118.177.7", 53)
    Write-Host "Port 53: Connected successfully"
    $stream = $tcp.GetStream()
    $buffer = New-Object byte[] 1024
    $stream.Read($buffer, 0, $buffer.Length) | Out-Null
    $tcp.Close()
} catch {
    Write-Host "Port 53 failed:" $_.Exception.Message
}

$tcp2 = New-Object System.Net.Sockets.TcpClient
$tcp2.SendTimeout = 5000
$tcp2.ReceiveTimeout = 5000
try {
    $tcp2.Connect("161.118.177.7", 443)
    Write-Host "Port 443: Connected successfully"
    $tcp2.Close()
} catch {
    Write-Host "Port 443 failed:" $_.Exception.Message
}