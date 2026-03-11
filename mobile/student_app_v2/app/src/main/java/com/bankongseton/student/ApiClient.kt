package com.bankongseton.student

import okhttp3.OkHttpClient
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
        @Query("limit") limit: Int = 50
    ): Call<TransactionsResponse>
    
    @POST("users/fcm-token")
    fun registerFCMToken(
        @Header("Authorization") token: String,
        @Body request: FCMTokenRequest
    ): Call<MessageResponse>
    
    @POST("auth/logout")
    fun logout(@Header("Authorization") token: String): Call<MessageResponse>

    @POST("nfc/register")
    suspend fun registerNfcDevice(
        @Header("Authorization") token: String,
        @Body request: NfcDeviceRequest
    ): retrofit2.Response<NfcRegisterResponse>

    @POST("nfc/unregister")
    suspend fun unregisterNfcDevice(
        @Header("Authorization") token: String,
        @Body request: NfcUnregisterRequest
    ): retrofit2.Response<MessageResponse>
}

object ApiClient {
    private const val BASE_URL = "https://juley2823.pythonanywhere.com/api/"
    
    private val client = OkHttpClient.Builder()
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
