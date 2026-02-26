package com.bankongseton.student.ui.screens

import android.widget.Toast
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.google.accompanist.swiperefresh.SwipeRefresh
import com.google.accompanist.swiperefresh.rememberSwipeRefreshState
import com.bankongseton.student.ApiClient
import com.bankongseton.student.SecureStorage
import com.bankongseton.student.Transaction
import com.bankongseton.student.TransactionItem
import com.bankongseton.student.ui.theme.BankongSetonTheme
import kotlinx.coroutines.launch

@Composable
fun TransactionsScreen() {
    val context = LocalContext.current
    val storage = remember { SecureStorage(context) }
    val scope = rememberCoroutineScope()
    
    var transactions by remember { mutableStateOf<List<Transaction>>(emptyList()) }
    var isRefreshing by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(true) }

    fun loadTransactions() {
        val token = storage.getToken() ?: return
        
        isRefreshing = true
        scope.launch {
            try {
                val response = ApiClient.api.getTransactions("Bearer $token")
                transactions = response.transactions
            } catch (e: Exception) {
                Toast.makeText(context, "Error loading transactions: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                isRefreshing = false
                isLoading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        loadTransactions()
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.surface
    ) {
        SwipeRefresh(
            state = rememberSwipeRefreshState(isRefreshing),
            onRefresh = { loadTransactions() }
        ) {
            if (isLoading) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (transactions.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        text = "No transactions yet",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(transactions) { transaction ->
                        TransactionCard(transaction)
                    }
                }
            }
        }
    }
}

@Composable
fun TransactionCard(transaction: Transaction) {
    var expanded by remember { mutableStateOf(false) }
    val items = transaction.items ?: emptyList()
    val hasItems = items.isNotEmpty()

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .animateContentSize()
            .then(
                if (hasItems) Modifier.clickable { expanded = !expanded }
                else Modifier
            ),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = transaction.timestamp,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = transaction.type,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "₱${String.format("%.2f", transaction.amount)}",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.error
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Balance: ₱${String.format("%.2f", transaction.balance)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                if (hasItems) {
                    Icon(
                        imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = if (expanded) "Collapse" else "Expand",
                        modifier = Modifier
                            .align(Alignment.CenterVertically)
                            .padding(start = 8.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            if (expanded && hasItems) {
                Spacer(modifier = Modifier.height(16.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface
                    )
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(
                            text = "Items:",
                            style = MaterialTheme.typography.titleSmall,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                        items.forEach { item ->
                            Text(
                                text = "${item.name} x${item.quantity} - ₱${String.format("%.2f", item.price * item.quantity)}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurface,
                                modifier = Modifier.padding(vertical = 4.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun TransactionCardPreview() {
    BankongSetonTheme {
        val sampleTransaction = Transaction(
            timestamp = "2024-02-03 14:30:00",
            type = "Purchase",
            amount = -75.50,
            balance = 924.50,
            description = "Purchase - Completed",
            items = listOf(
                TransactionItem(name = "Burger", price = 50.0, quantity = 1),
                TransactionItem(name = "Coke", price = 25.5, quantity = 1)
            )
        )
        TransactionCard(transaction = sampleTransaction)
    }
}

@Preview(showBackground = true)
@Composable
fun TransactionCardNoItemsPreview() {
    BankongSetonTheme {
        val sampleTransaction = Transaction(
            timestamp = "2024-02-03 10:15:00",
            type = "Deposit",
            amount = 500.0,
            balance = 1500.0,
            description = "Deposit - Completed",
            items = null
        )
        TransactionCard(transaction = sampleTransaction)
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun TransactionsScreenPreview() {
    BankongSetonTheme {
        Surface(color = MaterialTheme.colorScheme.surface) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(3) { index ->
                    val transaction = when (index) {
                        0 -> Transaction(
                            timestamp = "2024-02-03 14:30:00",
                            type = "Purchase",
                            amount = -75.50,
                            balance = 924.50,
                            description = "Purchase - Completed",
                            items = listOf(
                                TransactionItem(name = "Burger", price = 50.0, quantity = 1),
                                TransactionItem(name = "Coke", price = 25.5, quantity = 1)
                            )
                        )
                        1 -> Transaction(
                            timestamp = "2024-02-02 09:15:00",
                            type = "Deposit",
                            amount = 500.0,
                            balance = 1000.0,
                            description = "Deposit - Completed",
                            items = null
                        )
                        else -> Transaction(
                            timestamp = "2024-02-01 16:45:00",
                            type = "Purchase",
                            amount = -150.0,
                            balance = 500.0,
                            description = "Purchase - Completed",
                            items = listOf(
                                TransactionItem(name = "Notebook", price = 75.0, quantity = 2)
                            )
                        )
                    }
                    TransactionCard(transaction = transaction)
                }
            }
        }
    }
}
