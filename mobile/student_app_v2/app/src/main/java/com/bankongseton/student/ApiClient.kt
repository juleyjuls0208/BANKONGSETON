package com.bankongseton.student

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Call
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface BangkoApiService {
    
    @POST("auth/login")
    fun login(@Body request: LoginRequest): Call<LoginResponse>
    
    @GET("student/balance")
    fun getBalance(@Header("Authorization") token: String): Call<Balance>
    
    @GET("student/transactions")
    fun getTransactions(
        @Header("Authorization") token: String,
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Call<TransactionsResponse>
    
    @POST("users/fcm-token")
    fun registerFCMToken(
        @Header("Authorization") token: String,
        @Body request: FCMTokenRequest
    ): Call<MessageResponse>
    
    @POST("auth/logout")
    fun logout(@Header("Authorization") token: String): Call<MessageResponse>
}

object ApiClient {
    private const val BASE_URL = "http://192.168.68.122:5001/api/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: BangkoApiService = retrofit.create(BangkoApiService::class.java)
}
