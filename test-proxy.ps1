try {
    $w = New-Object System.Net.Sockets.TcpClient('161.118.177.7', 9000)
    $s = $w.GetStream()
    $b = [byte[]][Text.Encoding]::ASCII.GetBytes("HELLO")
    $s.Write($b, 0, $b.Length)
    $s.Flush()
    $r = New-Object byte[] 1024
    $n = $s.Read($r, 0, $r.Length)
    $output = [Text.Encoding]::ASCII.GetString($r, 0, $n)
    Write-Host "Response: $output"
    $w.Close()
} catch {
    Write-Host "Failed: $($_.Exception.Message)"
}