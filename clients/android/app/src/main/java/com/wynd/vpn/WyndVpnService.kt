package com.wynd.vpn

import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.ParcelFileDescriptor
import kotlinx.coroutines.*
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.Socket
import java.nio.ByteBuffer

class WyndVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private var tcpSocket: Socket? = null
    private var serverJob: Job? = null
    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    companion object {
        private const val SERVER_HOST = "161.118.177.7"
        private const val SERVER_PORT = 53  // Production port
        private const val MTU = 1500
    }

    override fun onCreate() {
        super.onCreate()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(1, createNotification())
        startVpn()
        return START_STICKY
    }

    override fun onDestroy() {
        stopVpn()
        super.onDestroy()
    }

    private fun startVpn() {
        try {
            // Create the TUN interface
            val builder = Builder()
                .setSession("WYND VPN")
                .addAddress("10.8.0.2", 32)
                .addRoute("0.0.0.0", 0)
                .addDnsServer("8.8.8.8")
                .setMtu(MTU)
                .setConfigureIntent(createConfigureIntent())

            vpnInterface = builder.establish()

            if (vpnInterface == null) {
                stopSelf()
                return
            }

            // Start the VPN tunnel
            startTunnel()

        } catch (e: Exception) {
            e.printStackTrace()
            stopSelf()
        }
    }

    private fun startTunnel() {
        serverJob = serviceScope.launch {
            try {
                // Connect to the server
                tcpSocket = Socket(SERVER_HOST, SERVER_PORT)
                tcpSocket?.soTimeout = 0

                val inputStream = tcpSocket!!.getInputStream()
                val outputStream = tcpSocket!!.getOutputStream()

                val vpnFd = vpnInterface!!
                val input = FileInputStream(vpnFd.fileDescriptor)
                val output = FileOutputStream(vpnFd.fileDescriptor)

                // Start two coroutines: one for reading from TUN and writing to TCP,
                // and one for reading from TCP and writing to TUN
                val readFromVpnJob = launch {
                    readFromVpn(outputStream)
                }

                val readFromServerJob = launch {
                    readFromServer(inputStream, output)
                }

                // Wait for both to complete
                readFromVpnJob.join()
                readFromServerJob.join()

            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                stopSelf()
            }
        }
    }

    private suspend fun readFromVpn(outputStream: java.io.OutputStream) {
        val buffer = ByteBuffer.allocate(MTU)
        val input = FileInputStream(vpnInterface!!.fileDescriptor)

        try {
            while (true) {
                val length = input.read(buffer.array())
                if (length <= 0) break

                // Frame the packet with 2-byte length header (Big Endian)
                val lengthBytes = ByteBuffer.allocate(2).putShort(length.toShort()).array()
                outputStream.write(lengthBytes)
                outputStream.write(buffer.array(), 0, length)
                outputStream.flush()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private suspend fun readFromServer(inputStream: java.io.InputStream, output: FileOutputStream) {
        val lengthBuffer = ByteArray(2)
        val payloadBuffer = ByteArray(MTU)

        try {
            while (true) {
                // Read 2-byte length header
                val headerRead = inputStream.read(lengthBuffer)
                if (headerRead != 2) break

                val payloadLength = ((lengthBuffer[0].toInt() and 0xFF) shl 8) or (lengthBuffer[1].toInt() and 0xFF)

                // Read the payload
                var totalRead = 0
                while (totalRead < payloadLength) {
                    val read = inputStream.read(payloadBuffer, totalRead, payloadLength - totalRead)
                    if (read <= 0) break
                    totalRead += read
                }

                // Write to the TUN interface
                output.write(payloadBuffer, 0, payloadLength)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun stopVpn() {
        serverJob?.cancel()
        serviceScope.cancel()

        try {
            tcpSocket?.close()
        } catch (e: Exception) { }

        try {
            vpnInterface?.close()
        } catch (e: Exception) { }

        vpnInterface = null
        tcpSocket = null
    }

    private fun createNotification(): android.app.Notification {
        val channel = android.app.NotificationChannel("wynd_vpn", "WYND VPN", android.app.NotificationManager.IMPORTANCE_LOW)
        val notificationManager = getSystemService(android.app.NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)

        return android.app.Notification.Builder(this, "wynd_vpn")
            .setContentTitle("WYND VPN Connected")
            .setContentText("Tunneling traffic over TCP 53")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .build()
    }

    private fun createConfigureIntent(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java)
        return PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}