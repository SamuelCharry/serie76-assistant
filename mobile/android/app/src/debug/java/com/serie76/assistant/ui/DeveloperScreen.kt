@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.serie76.assistant.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.serie76.assistant.BuildConfig
import com.serie76.assistant.data.*
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import retrofit2.http.GET
import retrofit2.http.Path

private interface DebugApi {
    @GET("api/messages/{id}/debug") suspend fun trace(@Path("id") id: String): DebugResponse
}

@Composable
fun DeveloperEntry(onOpen: () -> Unit) {
    TextButton(colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onPrimaryContainer), onClick = onOpen) { Text("Developer debug") }
}

@Composable
fun DeveloperScreen(state: AppState, onBack: () -> Unit, onChoose: (String) -> Unit,
                    loadTrace: (suspend (String) -> DebugResponse)? = null) {
    val authenticated = LocalAuthenticatedApi.current
    val api = remember(authenticated) { (authenticated ?: createRetrofit(BuildConfig.BACKEND_URL)).create(DebugApi::class.java) }
    val answers = state.messages.filter { it.role == "assistant" }
    val selected = state.debugMessageId?.takeIf { id -> answers.any { it.id == id } } ?: answers.lastOrNull()?.id
    var trace by remember(selected) { mutableStateOf<DebugResponse?>(null) }
    var error by remember(selected) { mutableStateOf<String?>(null) }
    var loading by remember(selected) { mutableStateOf(false) }
    var attempt by remember { mutableIntStateOf(0) }
    LaunchedEffect(selected, attempt) {
        if (selected == null) return@LaunchedEffect
        loading = true; error = null; trace = null
        try { trace = loadTrace?.invoke(selected) ?: api.trace(selected) }
        catch (cancel: CancellationException) { throw cancel }
        catch (_: Exception) { error = "Trace unavailable. Check backend connectivity and DEV_DEBUG=true." }
        finally { loading = false }
    }
    Scaffold(topBar = {
        TopAppBar(title = { Text("Developer debug") }, navigationIcon = {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back to chat") }
        })
    }) { insets ->
        LazyColumn(Modifier.fillMaxSize().padding(insets), contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            item { Text("Real tool calls for each saved response. Development build only.", style = MaterialTheme.typography.bodyMedium) }
            if (answers.isEmpty()) item { EmptyState("No responses yet", "Return to the chat and send a question first.") }
            items(answers, key = Message::id) { message ->
                OutlinedButton(colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onPrimaryContainer), onClick = { onChoose(message.id) }, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.fillMaxWidth()) {
                        Text(if (message.id == selected) "Selected response" else "Inspect response", style = MaterialTheme.typography.labelLarge)
                        Text(message.content.take(160), style = MaterialTheme.typography.bodySmall, maxLines = 3)
                    }
                }
            }
            if (loading) item { LoadingLine("Loading tool calls") }
            error?.let { item { ErrorPanel(it, "Try again", { attempt++ }) } }
            trace?.let { response ->
                if (response.toolCalls.isEmpty()) item { Text("No tools were called for this response.") }
                items(response.toolCalls.withIndex().toList(), key = { it.index }) { (_, call) ->
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(call.name, style = MaterialTheme.typography.titleMedium)
                        Text("Parameters", style = MaterialTheme.typography.labelLarge)
                        JsonBlock(call.parameters)
                        Text("Returned data", style = MaterialTheme.typography.labelLarge)
                        JsonBlock(call.data)
                    }
                }
            }
        }
    }
}

@Composable
private fun JsonBlock(value: JsonElement) {
    val formatted = remember(value) { Json { prettyPrint = true }.encodeToString(JsonElement.serializer(), value) }
    SelectionContainer {
        Text(formatted, Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(8.dp),
            style = MaterialTheme.typography.bodySmall, fontFamily = FontFamily.Monospace)
    }
}
