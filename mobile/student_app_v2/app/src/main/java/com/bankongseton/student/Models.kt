package com.bankongseton.student

import com.google.gson.annotations.SerializedName

// Request/Response Models
data class LoginRequest(
    @SerializedName("student_id") val studentId: String
)

data class LoginResponse(
    val token: String,
    val student: Student,
    @SerializedName("jwt_token") val jwtToken: String? = null
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
    val count: Int
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
    val error: String? = null,
    val message: String? = null
)

data class NfcDeviceRequest(
    @SerializedName("device_id") val deviceId: String,
    val pin: String
)

data class NfcUnregisterRequest(
    @SerializedName("device_id") val deviceId: String
)

data class NfcRegisterResponse(
    @SerializedName("virtual_card_token") val virtual_card_token: String,
    val message: String
)

data class LostCardStatusResponse(
    val reported: Boolean,
    val processed: Boolean,
    @SerializedName("report_id") val reportId: String?
)

data class QrCartItem(
    val name: String,
    val price: Double,
    val qty: Int = 1
)

data class QrCartResponse(
    val items: List<QrCartItem>,
    val total: Double,
    val cashier: String
)

data class QrConfirmRequest(
    val token: String
)

data class QrConfirmResponse(
    val message: String,
    @SerializedName("new_balance") val newBalance: Double
)
