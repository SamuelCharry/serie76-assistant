@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.serie76.assistant.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import android.content.ClipData
import androidx.compose.ui.platform.ClipEntry
import androidx.compose.ui.platform.LocalClipboard
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.serie76.assistant.BuildConfig
import com.serie76.assistant.data.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import retrofit2.HttpException
import retrofit2.http.GET
import retrofit2.http.Path

interface DebugApi {
    @GET("api/messages/{id}/debug") suspend fun trace(@Path("id") id: String): DebugResponse
}

@Composable
fun DeveloperSheet(message: Message, onDismiss: () -> Unit,
                   loadTrace: (suspend (String) -> DebugResponse)? = null) {
    // Defense in depth: callers cannot accidentally expose a developer sheet in normal mode.
    if (!showDebugDetails(LocalDeveloperMode.current.enabled, message)) return
    val authenticated = LocalAuthenticatedApi.current
    val api = remember(authenticated) { (authenticated ?: createRetrofit(BuildConfig.BACKEND_URL)).create(DebugApi::class.java) }
    var trace by remember(message.id) { mutableStateOf<DebugResponse?>(null) }
    var error by remember(message.id) { mutableStateOf<String?>(null) }
    var disabled by remember(message.id) { mutableStateOf(false) }
    var loading by remember(message.id) { mutableStateOf(true) }
    var attempt by remember(message.id) { mutableIntStateOf(0) }
    LaunchedEffect(message.id, attempt) {
        loading = true; error = null; disabled = false; trace = null
        try {
            val response = loadTrace?.invoke(message.id) ?: api.trace(message.id)
            if (response.messageId != message.id) error = "Debug response did not match this answer."
            else trace = response
        } catch (cancel: CancellationException) { throw cancel }
        catch (failure: HttpException) {
            if (failure.code() == 404) disabled = true else error = failureMessage(failure)
        } catch (failure: Exception) { error = failureMessage(failure) }
        finally { loading = false }
    }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)) {
        LazyColumn(Modifier.fillMaxWidth().weight(1f, fill = false), contentPadding = PaddingValues(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Text("Debug details", style = MaterialTheme.typography.titleLarge) }
            item { Text(message.content.take(240), style = MaterialTheme.typography.bodySmall, maxLines = 4) }
            if (loading) item { LoadingLine("Loading debug details") }
            if (disabled) item { Text(DEBUG_DISABLED) }
            error?.let { detail -> item { ErrorPanel(detail, "Try again", { attempt++ }) } }
            trace?.let { response ->
                if (response.toolCalls.isEmpty()) item { Text("No tools were called for this response.") }
                items(debugSections(response), key = DebugSection::id) { section -> DebugSectionContent(section) }
            }
            item { TextButton(onClick = onDismiss) { Text("Close") } }
        }
    }
}

@Composable
private fun DebugSectionContent(section: DebugSection) {
    var expanded by remember(section.id) { mutableStateOf(false) }
    Column {
        TextButton(onClick = { expanded = !expanded }, modifier = Modifier.fillMaxWidth()) {
            Text("${if (expanded) "▾" else "▸"} ${section.title}", Modifier.fillMaxWidth(), style = MaterialTheme.typography.labelLarge)
        }
        if (expanded) JsonBlock(section.value)
    }
}

private val prettyJson = Json { prettyPrint = true }

/** Reuses the former developer screen's selectable, horizontally scrollable monospace JSON. */
@Composable
private fun JsonBlock(value: JsonElement) {
    val formatted = remember(value) { prettyJson.encodeToString(JsonElement.serializer(), value) }
    val clipboard = LocalClipboard.current
    val scope = rememberCoroutineScope()
    TextButton(onClick = { scope.launch { clipboard.setClipEntry(ClipEntry(ClipData.newPlainText("Debug JSON", formatted))) } }) { Text("Copy JSON") }
    SelectionContainer {
        Text(formatted, Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(8.dp),
            style = MaterialTheme.typography.bodySmall, fontFamily = FontFamily.Monospace)
    }
}
