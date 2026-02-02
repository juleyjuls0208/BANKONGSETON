package com.juls.bankongsetonandroid

data class Transaction(
    val timestamp: String,
    val type: String,
    val amount: Double,
    val balance: Double,
    val description: String
)
