package com.serie76.assistant.ui

import android.database.ContentObserver
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.compose.animation.core.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.text
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.font.FontWeight
import kotlin.math.PI
import kotlin.math.cos

@Composable
private fun motionEnabled(): Boolean {
    val resolver = LocalContext.current.contentResolver
    fun enabled() = Settings.Global.getFloat(resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) > 0f
    var value by remember(resolver) { mutableStateOf(enabled()) }
    DisposableEffect(resolver) {
        val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
            override fun onChange(selfChange: Boolean) { value = enabled() }
        }
        resolver.registerContentObserver(Settings.Global.getUriFor(Settings.Global.ANIMATOR_DURATION_SCALE), false, observer)
        onDispose { resolver.unregisterContentObserver(observer) }
    }
    return value
}

@Composable
fun HelloGreeting(modifier: Modifier = Modifier) {
    val enabled = motionEnabled()
    val reveal = remember { Animatable(if (enabled) 0f else 1f) }
    LaunchedEffect(enabled) {
        if (enabled) reveal.animateTo(1f, tween(640, easing = CubicBezierEasing(0.22f, 1f, 0.36f, 1f)))
        else reveal.snapTo(1f)
    }
    val tones = if (LocalAppearance.current.dark)
        listOf(Color(0xFFE3D6F1), Color(0xFFCDB9E1), Color(0xFFBAA5D6), Color(0xFFCDB9E1), Color(0xFFE3D6F1))
    else listOf(Color(0xFF62546F), Color(0xFF736181), Color(0xFF7D6B8D), Color(0xFF736181), Color(0xFF62546F))
    Text(buildAnnotatedString {
        "Hello".forEachIndexed { index, letter ->
            val amount = ((reveal.value * 7f - index) / 3f).coerceIn(0f, 1f)
            withStyle(SpanStyle(color = tones[index].copy(alpha = 0.35f + 0.65f * amount),
                baselineShift = BaselineShift((1f - amount) * 0.1f))) { append(letter) }
        }
    }, modifier.clearAndSetSemantics { text = AnnotatedString("Hello"); heading() },
        style = MaterialTheme.typography.displaySmall.copy(fontWeight = FontWeight.Medium),
        textAlign = TextAlign.Center)
}

@Composable
fun ThinkingLabel(modifier: Modifier = Modifier) {
    val enabled = motionEnabled()
    val dark = LocalAppearance.current.dark
    val phase = if (enabled) {
        val transition = rememberInfiniteTransition(label = "Waiting text")
        val value by transition.animateFloat(0f, 1f,
            infiniteRepeatable(tween(1500, easing = LinearEasing)), label = "Letter wave")
        value
    } else 0f
    Text(buildAnnotatedString {
        "Thinking…".forEachIndexed { index, letter ->
            val amount = if (enabled) ((1.0 + cos((phase * 2.0 - index * 0.14) * PI)) / 2.0).toFloat() else 0f
            withStyle(SpanStyle(color = if (dark) lerp(Color(0xFFB9AEC5), Color(0xFFEFE9F6), amount)
                else lerp(Color(0xFF5F556B), Color(0xFF7B6B86), amount))) { append(letter) }
        }
    }, modifier.clearAndSetSemantics { text = AnnotatedString("Thinking…"); liveRegion = LiveRegionMode.Polite },
        style = MaterialTheme.typography.bodyLarge)
}
