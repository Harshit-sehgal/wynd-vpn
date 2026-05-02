$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.SendTimeout = 3000
$tcp.ReceiveTimeout = 3000
try {
    $tcp.Connect("161.118.177.7", 53)
    Write-Host "Connected to port 53"
    $tcp.Close()
} catch {
    Write-Host "Failed:" $_.Exception.Message
}