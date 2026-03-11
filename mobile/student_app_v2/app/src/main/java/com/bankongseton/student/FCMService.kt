package com.bankongseton.student

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class FCMService : FirebaseMessagingService() {
    
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Save token locally for registration on next login
        getSharedPreferences("bangko_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString("fcm_token", token)
            .apply()
        // If already logged in, register immediately
        val secureStorage = SecureStorage(this)
        val authToken = secureStorage.getAuthToken()
        if (!authToken.isNullOrEmpty()) {
            ApiClient.apiService.registerFCMToken(
                "Bearer $authToken",
                FCMTokenRequest(token)
            ).enqueue(object : retrofit2.Callback<MessageResponse> {
                override fun onResponse(call: retrofit2.Call<MessageResponse>, response: retrofit2.Response<MessageResponse>) {}
                override fun onFailure(call: retrofit2.Call<MessageResponse>, t: Throwable) {}
            })
        }
    }
    
    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        // Handle data messages (e.g. card_replaced)
        val msgType = message.data["type"]
        if (msgType == "card_replaced") {
            // Clear lost card state so HomeActivity shows "Resolved"
            val secureStorage = SecureStorage(this)
            secureStorage.clearLostCardReported()
            // Also show a notification
            showNotification(
                title = message.notification?.title ?: "Card Replacement Ready",
                body = message.notification?.body ?: "Your new card has been activated."
            )
            return
        }

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
