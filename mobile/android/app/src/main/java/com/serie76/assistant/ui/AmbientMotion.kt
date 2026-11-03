package com.serie76.assistant.ui

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.PowerManager
import android.os.SystemClock
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

/** Decorative motion never competes with reading, input, or device power policy. */
@Composable
internal fun rememberAmbientPhase(visible: Boolean): State<Float> {
    val context = LocalContext.current
    val power = remember(context) { context.getSystemService(PowerManager::class.java) }
    var savingPower by remember(power) { mutableStateOf(power.isPowerSaveMode) }
    DisposableEffect(context, power) {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) { savingPower = power.isPowerSaveMode }
        }
        // System-only broadcast: no exported app command or custom receiver surface.
        context.registerReceiver(receiver, IntentFilter(PowerManager.ACTION_POWER_SAVE_MODE_CHANGED))
        onDispose { context.unregisterReceiver(receiver) }
    }
    return ambientClock(visible && motionEnabled() && !savingPower)
}

/** Read only in draw/layer lambdas: ticking does not recompose or relayout chat. */
@Composable
internal fun ambientClock(running: Boolean): State<Float> {
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val phase = remember { mutableFloatStateOf(0f) }
    LaunchedEffect(lifecycle, running) {
        if (running) lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
            var previous = SystemClock.elapsedRealtime()
            while (isActive) {
                delay(50L) // At most 20 updates/s, independent of a 60/120 Hz display.
                val now = SystemClock.elapsedRealtime()
                phase.floatValue = (phase.floatValue + (now - previous) / 32000f) % 1f
                previous = now
            }
        }
    }
    return phase
}
