package com.example.gmap

import android.content.Intent
import android.net.Uri // 추가
import android.content.pm.PackageManager // 추가
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    companion object {
        var MyTTSServiceInstance: MyTTSService? = null
    }

    private val CHANNEL = "my_tts_channel"
    private val NAVER_MAP_CHANNEL = "com.example.gmap/naver_map"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when(call.method) {
                    "startTTSService" -> {
                        val intent = Intent(this, MyTTSService::class.java)
                        startForegroundService(intent)
                        result.success(null)
                    }
                    "speakText" -> {
                        val text = call.argument<String>("text") ?: ""
                        MyTTSServiceInstance?.speak(text)
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
        // 네이버 지도 앱 호출 관련 채널 설정
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, NAVER_MAP_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "openNaverMap" -> {
                        val uriString = call.argument<String>("uri")
                        if (uriString.isNullOrEmpty()) {
                            result.error("INVALID_ARGS", "URI is null or empty", null)
                            return@setMethodCallHandler
                        }
                        openNaverMapApp(uriString)
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
    }

    private fun openNaverMapApp(url: String) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
            addCategory(Intent.CATEGORY_BROWSABLE)
        }

        val pm = packageManager
        val list = pm.queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY)

        if (list == null || list.isEmpty()) {
            // 네이버 지도 앱 미설치 시 Play Store로 이동
            val marketIntent = Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=com.nhn.android.nmap"))
            startActivity(marketIntent)
        } else {
            startActivity(intent)
        }
    }
}
    