package com.example.gmap

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.speech.tts.TextToSpeech
import androidx.core.app.NotificationCompat
import java.util.*

class MyTTSService : Service(), TextToSpeech.OnInitListener {
    private lateinit var tts: TextToSpeech
    private var isTtsReady = false
    private val CHANNEL_ID = "tts_service_channel"
    private val NOTIFICATION_ID = 999

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification("TTS 서비스 실행 중"))
        tts = TextToSpeech(this, this)
        // MyTTSServiceInstance를 static하게 관리 (MainActivity에서 접근)
        MainActivity.MyTTSServiceInstance = this
    }

    override fun onDestroy() {
        tts.stop()
        tts.shutdown()
        MainActivity.MyTTSServiceInstance = null
        super.onDestroy()
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts.language = Locale.KOREAN
            isTtsReady = true
        }
    }

    fun speak(text: String) {
        if (isTtsReady) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "utteranceId")
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "TTS Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun createNotification(content: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("TTS Foreground Service")
            .setContentText(content)
            .setSmallIcon(android.R.drawable.ic_lock_silent_mode_off)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}