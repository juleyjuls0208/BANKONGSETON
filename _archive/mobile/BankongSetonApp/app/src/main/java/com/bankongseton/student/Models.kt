package com.bankongseton.student

import com.google.gson.annotations.SerializedName

// Login
data class LoginRequest(val studentId: String)

data class LoginResponse(
    val error: String?,
    val token: String?,
    val student: LoginStudent?
)

data class LoginStudent(
    val id: String,
    val name: String,
    @SerializedName("id_card") val idCard: String?,
    @SerializedName("money_card") val moneyCard: String?,
    val status: String?
)

// Balance
data class BalanceResponse(
    val balance: Double,
    @SerializedName("money_card") val moneyCard: String?
)

// Student for display (constructed from login + balance)
data class Student(
    val StudentId: String,
    val Name: String,
    val Balance: Double
)

// Transactions
data class TransactionsResponse(
    val transactions: List<Transaction>,
    val count: Int
)

data class Transaction(
    val timestamp: String,
    val type: String,
    val amount: Double,
    val balance: Double,
    val description: String?,
    val items: List<TransactionItem>?
)

data class TransactionItem(
    val name: String,
    val price: Double,
    val quantity: Int
)

// FCM Token
data class FCMTokenRequest(val fcmToken: String)

// Generic message response
data class MessageResponse(val message: String)
