package com.bankongseton.student

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class FCMService : FirebaseMessagingService() {
    
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Save token so LoginActivity can register it on next login
        val prefs = getSharedPreferences("bangko_prefs", Context.MODE_PRIVATE)
        prefs.edit().putString("fcm_token", token).apply()

        // If user is already logged in, register the new token with the backend immediately
        val authToken = SecureStorage(this).getAuthToken()
        if (!authToken.isNullOrEmpty()) {
            CoroutineScope(Dispatchers.IO).launch {
                try {
                    ApiClient.apiService.registerFCMToken(
                        "Bearer $authToken",
                        FCMTokenRequest(token)
                    ).execute()
                } catch (e: Exception) {
                    Log.w("FCMService", "FCM register failed: ${e.message}")
                }
            }
        }
    }
    
    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        
        message.notification?.let { notification ->
            showNotification(
                title = notification.title ?: "Bangko ng Seton",
                body = notification.body ?: ""
            )
        }
    }
    
    private fun showNotification(title: String, body: String) {
        val channelId = "bangko_notifications"
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Bangko Notifications",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            notificationManager.createNotificationChannel(channel)
        }
        
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()
        
        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
