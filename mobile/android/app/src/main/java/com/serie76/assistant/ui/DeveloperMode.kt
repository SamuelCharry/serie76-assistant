package com.serie76.assistant.ui

import android.content.Context
import android.widget.Toast
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext

data class DeveloperMode(val enabled: Boolean = false, val toggle: () -> Unit = {})
val LocalDeveloperMode = staticCompositionLocalOf { DeveloperMode() }

@Composable
fun DeveloperModeProvider(content: @Composable () -> Unit) {
    val context = LocalContext.current
    val preferences = remember(context) { context.getSharedPreferences("developer", Context.MODE_PRIVATE) }
    var enabled by remember(preferences) { mutableStateOf(preferences.getBoolean("enabled", false)) }
    CompositionLocalProvider(LocalDeveloperMode provides DeveloperMode(enabled) {
        enabled = !enabled
        preferences.edit().putBoolean("enabled", enabled).apply()
        Toast.makeText(context, if (enabled) "Developer mode on" else "Developer mode off", Toast.LENGTH_SHORT).show()
    }, content = content)
}
