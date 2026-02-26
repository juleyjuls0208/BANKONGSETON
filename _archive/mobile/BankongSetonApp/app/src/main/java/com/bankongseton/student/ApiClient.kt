package com.bankongseton.student

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor

interface BangkoApiService {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("student/balance")
    suspend fun getBalance(@Header("Authorization") token: String): BalanceResponse

    @GET("student/transactions")
    suspend fun getTransactions(@Header("Authorization") token: String, @Query("limit") limit: Int = 50): TransactionsResponse

    @POST("users/fcm-token")
    suspend fun registerFCM(@Header("Authorization") token: String, @Body request: FCMTokenRequest): MessageResponse
}

object ApiClient {
    // Server API Base URL - Update this to match your backend server IP
    // Online API: https://juley2823.pythonanywhere.com/api/
    // Local API: http://100.107.68.49:5001/api/
    private const val BASE_URL = "https://juley2823.pythonanywhere.com/api/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        // Use BASIC level for faster initialization (change to BODY for debugging)
        level = HttpLoggingInterceptor.Level.BASIC
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .retryOnConnectionFailure(true) // Add retry on connection failure
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val api: BangkoApiService = retrofit.create(BangkoApiService::class.java)
}
