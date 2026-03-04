package com.bankongseton.student

import com.google.gson.annotations.SerializedName

// Request/Response Models
data class LoginRequest(
    @SerializedName("student_id") val studentId: String
)

data class LoginResponse(
    val token: String,
    val student: Student
)

data class Student(
    val id: String,
    val name: String,
    @SerializedName("id_card") val idCard: String,
    @SerializedName("money_card") val moneyCard: String,
    val status: String
)

data class Balance(
    val balance: Double,
    @SerializedName("money_card") val moneyCard: String
)

data class TransactionsResponse(
    val transactions: List<Transaction>,
    val count: Int,
    val total: Int? = null,
    @SerializedName("has_more") val hasMore: Boolean? = null
)

data class Transaction(
    val timestamp: String,
    val type: String,
    val amount: Double,
    val balance: Double,
    @SerializedName("balance_before") val balanceBefore: Double = 0.0,
    val description: String,
    val items: List<TransactionItem>? = null
)

data class TransactionItem(
    val name: String,
    val price: Double,
    val qty: Int = 1
)

data class FCMTokenRequest(
    @SerializedName("fcm_token") val fcmToken: String
)

data class MessageResponse(
    val message: String
)

data class ErrorResponse(
    val error: String
)

// NFC Models
data class NfcDeviceRequest(val device_id: String, val pin: String)
data class NfcRegistrationResponse(val virtual_card_token: String)
data class NfcUnregisterRequest(val device_id: String)
