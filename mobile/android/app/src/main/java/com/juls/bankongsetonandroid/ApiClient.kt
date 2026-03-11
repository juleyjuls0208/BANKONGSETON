package com.juls.bankongsetonandroid

import android.content.Context
import android.content.SharedPreferences
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Call
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

// Data classes for API responses
data class LoginRequest(val student_id: String)

data class LoginResponse(
    val token: String,
    val student: StudentData
)

data class StudentData(
    @com.google.gson.annotations.SerializedName("student_id")
    val id: String,
    val name: String,
    val id_card: String,
    val money_card: String,
    val status: String
)

data class BalanceResponse(
    val balance: Double,
    val money_card: String
)

data class TransactionsResponse(
    val transactions: List<Transaction>,
    val count: Int
)

data class ApiError(val error: String)

// NFC Registration
data class NfcRegistrationRequest(
    val device_id: String,
    val device_name: String,
    val pin: String
)

data class NfcRegistrationResponse(
    val virtual_token: String,
    val expires_at: String
)

data class NfcUnregisterRequest(val device_id: String)

// Retrofit API Interface
interface BankoApiService {
    @POST("api/auth/login")
    fun login(@Body request: LoginRequest): Call<LoginResponse>
    
    @GET("api/student/profile")
    fun getProfile(@Header("Authorization") token: String): Call<StudentData>
    
    @GET("api/student/balance")
    fun getBalance(@Header("Authorization") token: String): Call<BalanceResponse>
    
    @GET("api/student/transactions")
    fun getTransactions(
        @Header("Authorization") token: String,
        @Query("limit") limit: Int = 50
    ): Call<TransactionsResponse>
    
    @POST("api/auth/logout")
    fun logout(@Header("Authorization") token: String): Call<Map<String, String>>
    
    // NFC Endpoints
    @POST("api/nfc/register")
    fun registerNfcDevice(
        @Header("Authorization") token: String,
        @Body request: NfcRegistrationRequest
    ): Call<NfcRegistrationResponse>
    
    @POST("api/nfc/unregister")
    fun unregisterNfcDevice(
        @Header("Authorization") token: String,
        @Body request: NfcUnregisterRequest
    ): Call<Map<String, String>>
    
    @GET("api/nfc/status")
    fun getNfcStatus(@Header("Authorization") token: String): Call<Map<String, Any>>
}

class ApiClient private constructor(context: Context) {
    
    private val prefs: SharedPreferences = 
        context.getSharedPreferences("banko_prefs", Context.MODE_PRIVATE)
    
    private val api: BankoApiService
    
    companion object {
        // TODO: Replace with your actual server URL
        private const val BASE_URL = "https://juley2823.pythonanywhere.com/" // Android emulator localhost
        // For physical device: "http://YOUR_SERVER_IP:5001/"
        
        @Volatile
        private var instance: ApiClient? = null
        
        fun getInstance(context: Context): ApiClient {
            return instance ?: synchronized(this) {
                instance ?: ApiClient(context.applicationContext).also { instance = it }
            }
        }
    }
    
    init {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
        
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        api = retrofit.create(BankoApiService::class.java)
    }
    
    // Session management
    fun saveToken(token: String) {
        prefs.edit().putString("auth_token", token).apply()
    }
    
    fun getToken(): String? {
        return prefs.getString("auth_token", null)
    }
    
    fun clearToken() {
        prefs.edit().remove("auth_token").apply()
    }
    
    fun isLoggedIn(): Boolean {
        return getToken() != null
    }
    
    private fun getAuthHeader(): String {
        return "Bearer ${getToken()}"
    }
    
    // API methods
    fun login(studentId: String): Call<LoginResponse> {
        return api.login(LoginRequest(studentId))
    }
    
    fun getProfile(): Call<StudentData> {
        return api.getProfile(getAuthHeader())
    }
    
    fun getBalance(): Call<BalanceResponse> {
        return api.getBalance(getAuthHeader())
    }
    
    fun getTransactions(limit: Int = 50): Call<TransactionsResponse> {
        return api.getTransactions(getAuthHeader(), limit)
    }
    
    fun logout(): Call<Map<String, String>> {
        return api.logout(getAuthHeader())
    }
    
    // NFC Methods
    fun registerNfcDevice(deviceId: String, deviceName: String, pin: String): Call<NfcRegistrationResponse> {
        return api.registerNfcDevice(getAuthHeader(), NfcRegistrationRequest(deviceId, deviceName, pin))
    }
    
    fun unregisterNfcDevice(deviceId: String): Call<Map<String, String>> {
        return api.unregisterNfcDevice(getAuthHeader(), NfcUnregisterRequest(deviceId))
    }
    
    fun getNfcStatus(): Call<Map<String, Any>> {
        return api.getNfcStatus(getAuthHeader())
    }
}

