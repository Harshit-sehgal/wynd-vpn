package com.wynd.vpn

import android.content.Intent
import android.net.VpnService
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var connectButton: Button
    private lateinit var statusText: TextView
    private var vpnService: WyndVpnService? = null

    companion object {
        private const val VPN_REQUEST_CODE = 100
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        connectButton = findViewById(R.id.connectButton)
        statusText = findViewById(R.id.statusText)

        connectButton.setOnClickListener {
            val intent = VpnService.prepare(this)
            if (intent != null) {
                startActivityForResult(intent, VPN_REQUEST_CODE)
            } else {
                startVpn()
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == VPN_REQUEST_CODE && resultCode == RESULT_OK) {
            startVpn()
        }
    }

    private fun startVpn() {
        val serviceIntent = Intent(this, WyndVpnService::class.java)
        startForegroundService(serviceIntent)
        statusText.text = "Status: Connecting..."
        connectButton.text = "Disconnect"
    }
}