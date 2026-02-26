package com.bankongseton.student.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.bankongseton.student.ApiClient
import com.bankongseton.student.LoginRequest
import com.bankongseton.student.SecureStorage
import com.bankongseton.student.ui.theme.BankongSetonTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(onLoginSuccess: () -> Unit) {
    val context = LocalContext.current
    val storage = remember { SecureStorage(context) }
    val scope = rememberCoroutineScope()
    
    var studentId by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.surface
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "Bangko ng Seton",
                style = MaterialTheme.typography.displaySmall,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.padding(bottom = 48.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.extraLarge,
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Column(
                    modifier = Modifier.padding(32.dp)
                ) {
                    Text(
                        text = "Student ID",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(bottom = 16.dp)
                    )

                    OutlinedTextField(
                        value = studentId,
                        onValueChange = { studentId = it },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("Enter your student ID") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
                        enabled = !isLoading
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    Button(
                        onClick = {
                            if (studentId.isBlank()) {
                                Toast.makeText(context, "Please enter your Student ID", Toast.LENGTH_SHORT).show()
                                return@Button
                            }
                            
                            isLoading = true
                            scope.launch(Dispatchers.IO) {
                                try {
                                    android.util.Log.d("LoginScreen", "Attempting login for: $studentId")
                                    
                                    val response = ApiClient.api.login(LoginRequest(studentId))
                                    
                                    android.util.Log.d("LoginScreen", "Response received - token: ${response.token}, error: ${response.error}")
                                    
                                    withContext(Dispatchers.Main) {
                                        if (response.token != null) {
                                            storage.saveToken(response.token)
                                            storage.saveStudentId(studentId)
                                            Toast.makeText(context, "Login successful!", Toast.LENGTH_SHORT).show()
                                            onLoginSuccess()
                                        } else {
                                            val errorMsg = response.error ?: "Login failed - no token received"
                                            android.util.Log.e("LoginScreen", "Login failed: $errorMsg")
                                            Toast.makeText(context, errorMsg, Toast.LENGTH_LONG).show()
                                        }
                                    }
                                } catch (e: retrofit2.HttpException) {
                                    val errorBody = e.response()?.errorBody()?.string()
                                    android.util.Log.e("LoginScreen", "HTTP Error: ${e.code()} - $errorBody")
                                    withContext(Dispatchers.Main) {
                                        Toast.makeText(context, "Server error: ${e.code()}", Toast.LENGTH_LONG).show()
                                    }
                                } catch (e: java.net.UnknownHostException) {
                                    android.util.Log.e("LoginScreen", "Network error: Cannot reach server", e)
                                    withContext(Dispatchers.Main) {
                                        Toast.makeText(context, "Cannot reach server", Toast.LENGTH_LONG).show()
                                    }
                                } catch (e: java.net.SocketTimeoutException) {
                                    android.util.Log.e("LoginScreen", "Connection timeout", e)
                                    withContext(Dispatchers.Main) {
                                        Toast.makeText(context, "Connection timeout", Toast.LENGTH_LONG).show()
                                    }
                                } catch (e: Exception) {
                                    android.util.Log.e("LoginScreen", "Login error", e)
                                    withContext(Dispatchers.Main) {
                                        Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_LONG).show()
                                    }
                                } finally {
                                    withContext(Dispatchers.Main) {
                                        isLoading = false
                                    }
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isLoading
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Text("Login", style = MaterialTheme.typography.titleMedium)
                        }
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun LoginScreenPreview() {
    BankongSetonTheme {
        LoginScreen(onLoginSuccess = {})
    }
}

@Preview(showBackground = true, showSystemUi = true, uiMode = android.content.res.Configuration.UI_MODE_NIGHT_YES)
@Composable
fun LoginScreenDarkPreview() {
    BankongSetonTheme(darkTheme = true) {
        LoginScreen(onLoginSuccess = {})
    }
}
