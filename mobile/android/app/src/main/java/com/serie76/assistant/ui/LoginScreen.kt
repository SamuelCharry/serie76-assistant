package com.serie76.assistant.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.*
import androidx.compose.ui.unit.dp
import com.serie76.assistant.data.Account
import retrofit2.Retrofit

data class AccountControls(val user: Account, val busy: Boolean, val error: String?, val logout: () -> Unit)
val LocalAccount = staticCompositionLocalOf<AccountControls?> { null }
val LocalAuthenticatedApi = staticCompositionLocalOf<Retrofit?> { null }

@Composable
fun LoginScreen(state: AuthState, onLogin: (String, String) -> Unit, onRetry: () -> Unit) {
    // Passwords never enter SavedStateHandle, rememberSaveable, preferences or logs.
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var visible by remember { mutableStateOf(false) }
    val keyboard = LocalSoftwareKeyboardController.current
    val submit = {
        if (email.isNotBlank() && password.isNotEmpty() && !state.busy && !state.checking) {
            val value = password
            password = ""
            keyboard?.hide()
            onLogin(email, value)
        }
    }
    Box(Modifier.fillMaxSize()) {
        ChatBackdrop(Modifier.fillMaxSize(), empty = false)
        Column(Modifier.fillMaxSize().safeDrawingPadding().imePadding().verticalScroll(rememberScrollState())
            .padding(horizontal = 28.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Column(Modifier.widthIn(max = 420.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(20.dp)) {
                Text("Welcome back", style = MaterialTheme.typography.displaySmall)
                Text("Sign in to your workspace.", style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (state.checking) {
                    LinearProgressIndicator(Modifier.fillMaxWidth())
                    Text("Checking your session", style = MaterialTheme.typography.bodyMedium)
                } else {
                    OutlinedTextField(email, { email = it.take(254) }, label = { Text("Email") }, singleLine = true,
                        enabled = !state.busy, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next),
                        modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Sign in email" })
                    OutlinedTextField(password, { password = it.take(1024) }, label = { Text("Password") }, singleLine = true,
                        enabled = !state.busy, visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Done),
                        keyboardActions = KeyboardActions(onDone = { submit() }),
                        trailingIcon = { TextButton(onClick = { visible = !visible }, enabled = !state.busy) { Text(if (visible) "Hide" else "Show") } },
                        modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Sign in password" })
                    state.error?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error) }
                    Button(onClick = { submit() }, enabled = email.isNotBlank() && password.isNotEmpty() && !state.busy,
                        shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp)) {
                        Text(if (state.busy) "Signing in…" else "Sign in")
                    }
                    if (state.canRetrySavedSession) TextButton(onClick = onRetry, enabled = !state.busy) { Text("Retry saved session") }
                }
            }
        }
    }
}
