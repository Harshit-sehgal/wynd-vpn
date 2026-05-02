$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.Connect('161.118.177.7', 444)
$stream = $tcp.GetStream()
$sw = New-Object System.IO.StreamWriter($stream)
$sw.WriteLine('HELLO')
$sw.Flush()
$sr = New-Object System.IO.StreamReader($stream)
$resp = $sr.ReadLine()
Write-Host "Response:" $resp
$tcp.Close()