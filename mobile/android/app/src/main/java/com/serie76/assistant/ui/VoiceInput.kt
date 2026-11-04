package com.serie76.assistant.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.delay

class VoiceInputControls(val state: VoiceState, val tap: () -> Unit, val cancel: () -> Unit)

@Composable
fun rememberVoiceInput(draft: String, enabled: Boolean, conversationId: String?, onDraft: (String) -> Unit): VoiceInputControls {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val latestDraft by rememberUpdatedState(draft)
    val latestEnabled by rememberUpdatedState(enabled)
    val updateDraft by rememberUpdatedState(onDraft)
    var state by remember { mutableStateOf(VoiceState()) }
    val controller = remember(context) { VoiceController({ createVoiceRecognizer(context) }, { state = it }, { updateDraft(it) }) }
    var rationale by remember { mutableStateOf(false) }
    var startAfterPermission by remember { mutableStateOf(false) }
    fun startIfForeground() {
        if (latestEnabled && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
            startAfterPermission = false
            controller.start(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED, latestDraft)
        }
    }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (!granted) controller.start(false, latestDraft)
        else { startAfterPermission = true; startIfForeground() }
    }
    DisposableEffect(lifecycle, controller) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_PAUSE) controller.cancel()
            if (event == Lifecycle.Event.ON_STOP) { startAfterPermission = false; rationale = false }
            if (event == Lifecycle.Event.ON_RESUME && startAfterPermission) startIfForeground()
        }
        lifecycle.addObserver(observer)
        onDispose { lifecycle.removeObserver(observer); controller.cancel() }
    }
    // Drawer, navigation, loading, sending, and changing threads all terminate the old microphone session.
    DisposableEffect(enabled, conversationId) {
        if (!enabled) { startAfterPermission = false; rationale = false; controller.cancel() }
        onDispose { startAfterPermission = false; controller.cancel() }
    }
    LaunchedEffect(state.phase) {
        if (state.active) {
            delay(if (state.phase == VoicePhase.FINISHING) 15000 else 60000)
            controller.timeout()
        }
    }
    if (rationale) AlertDialog(onDismissRequest = { rationale = false },
        title = { Text("Voice input") },
        text = { Text("Allow microphone access to turn your speech into text you can review before sending.") },
        confirmButton = { TextButton(onClick = { rationale = false; permission.launch(Manifest.permission.RECORD_AUDIO) }) { Text("Continue") } },
        dismissButton = { TextButton(onClick = { rationale = false }) { Text("Cancel") } })
    return VoiceInputControls(state, tap = {
        if (enabled) {
            if (state.active) controller.stop()
            else if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) rationale = true
            else startIfForeground()
        }
    }, cancel = { startAfterPermission = false; controller.cancel() })
}

@Composable
fun VoiceInputNotice(state: VoiceState) {
    val context = LocalContext.current
    state.error?.let { error ->
        Column {
            Text(error.message, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
            if (error == VoiceError.PERMISSION) TextButton(onClick = {
                context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:${context.packageName}")))
            }) { Text("Open settings") }
        }
    }
}

@Composable
fun VoiceInputButton(voice: VoiceInputControls) {
    val listening = voice.state.phase == VoicePhase.LISTENING
    val opacity = if (listening) {
        val transition = rememberInfiniteTransition(label = "Listening")
        val pulse by transition.animateFloat(0.55f, 1f,
            infiniteRepeatable(tween(900), RepeatMode.Reverse), label = "Microphone pulse")
        pulse
    } else 1f
    IconButton(onClick = voice.tap, enabled = voice.state.phase != VoicePhase.FINISHING, modifier = Modifier.size(48.dp)) {
        Icon(MicrophoneLines, if (voice.state.active) "Stop listening" else "Voice input",
            Modifier.size(24.dp).alpha(opacity),
            tint = if (listening) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

private val MicrophoneLines = ImageVector.Builder("Microphone", 24.dp, 24.dp, 24f, 24f).apply {
    path(stroke = SolidColor(Color.Black), strokeLineWidth = 1.7f) {
        moveTo(9f, 5f); curveTo(9f, 1f, 15f, 1f, 15f, 5f); lineTo(15f, 11f)
        curveTo(15f, 15f, 9f, 15f, 9f, 11f); close()
        moveTo(5f, 10f); lineTo(5f, 11f); curveTo(5f, 20f, 19f, 20f, 19f, 11f); lineTo(19f, 10f)
        moveTo(12f, 18f); lineTo(12f, 22f); moveTo(8f, 22f); lineTo(16f, 22f)
    }
}.build()
