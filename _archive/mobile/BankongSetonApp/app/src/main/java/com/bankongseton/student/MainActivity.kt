package com.bankongseton.student

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bankongseton.student.ui.screens.HomeScreen
import com.bankongseton.student.ui.screens.LoginScreen
import com.bankongseton.student.ui.screens.SettingsScreen
import com.bankongseton.student.ui.screens.TransactionsScreen
import com.bankongseton.student.ui.theme.BankongSetonTheme
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Pre-initialize ApiClient on IO thread to avoid blocking later
        CoroutineScope(Dispatchers.IO).launch {
            try {
                android.util.Log.d("MainActivity", "Pre-initializing ApiClient...")
                ApiClient.api // Access to trigger initialization
                android.util.Log.d("MainActivity", "ApiClient initialized successfully")
            } catch (e: Exception) {
                android.util.Log.e("MainActivity", "Failed to initialize ApiClient", e)
            }
        }
        
        val storage = SecureStorage(this)
        val token = storage.getToken()
        val startDestination = if (token != null) "home" else "login"
        
        setContent {
            BankongSetonTheme {
                AppNavigation(startDestination)
            }
        }
    }
}

@Composable
fun AppNavigation(startDestination: String) {
    val navController = rememberNavController()
    
    NavHost(navController = navController, startDestination = startDestination) {
        composable("login") {
            LoginScreen(onLoginSuccess = {
                navController.navigate("home") {
                    popUpTo("login") { inclusive = true }
                }
            })
        }
        composable("home") {
            HomeScreen(
                onNavigateToTransactions = { navController.navigate("transactions") },
                onNavigateToSettings = { navController.navigate("settings") }
            )
        }
        composable("transactions") {
            TransactionsScreen()
        }
        composable("settings") {
            SettingsScreen(onLogout = {
                navController.navigate("login") {
                    popUpTo(0) { inclusive = true }
                }
            })
        }
    }
}