package com.serie76.assistant.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.serie76.assistant.R
import kotlin.math.PI
import kotlin.math.sin
import kotlin.math.cos

/** Cached brand mesh and twelve quiet motes; no animation behind technical content. */
@Composable
fun ChatBackdrop(modifier: Modifier = Modifier, empty: Boolean) {
    val dark = LocalAppearance.current.dark
    val phase = rememberAmbientPhase(empty)
    Box(modifier) {
        Canvas(Modifier.fillMaxSize()) {
            drawRect(if (dark) Color(0xFF101014) else Color(0xFFFCFCFD))
            drawRect(Brush.radialGradient(
                listOf((if (dark) Color(0xFF592D80) else Color(0xFFECE2FA))
                    .copy(alpha = if (empty) { if (dark) 0.6f else 0.85f } else 0.25f), Color.Transparent),
                center = Offset(size.width * 1.02f, size.height * 0.48f), radius = size.width * 1.22f))
            drawRect(Brush.radialGradient(
                listOf((if (dark) Color(0xFF33204E) else Color(0xFFF3EAFB))
                    .copy(alpha = if (empty) 0.8f else 0.25f), Color.Transparent),
                center = Offset(-size.width * 0.15f, size.height * 0.82f), radius = size.width * 0.95f))
        }
        if (empty) Image(painterResource(R.drawable.konecto_wave), contentDescription = null,
            modifier = Modifier.fillMaxWidth().height(320.dp).align(Alignment.BottomCenter).offset(y = (-38).dp)
                .graphicsLayer {
                    translationX = sin(phase.value * 2f * PI).toFloat() * 3.dp.toPx()
                    translationY = (cos(phase.value * 2f * PI).toFloat() - 1f) * 2.dp.toPx()
                },
            contentScale = ContentScale.Crop, colorFilter = ColorFilter.tint(Color(0xFFAD94C5)), alpha = if (dark) 0.24f else 0.32f)
        if (empty) Canvas(Modifier.fillMaxWidth().height(320.dp).align(Alignment.BottomCenter).offset(y = (-38).dp)) {
            val angle = phase.value * 2f * PI
            repeat(12) { index ->
                val seed = index * 2.399963
                val x = size.width * (0.08f + ((index * 37) % 89) / 100f) + sin(angle + seed).toFloat() * 10.dp.toPx()
                val y = size.height * (0.14f + ((index * 23) % 73) / 100f) + cos(angle + seed).toFloat() * 14.dp.toPx()
                drawCircle(Color(0xFFAD94C5).copy(alpha = if (dark) 0.38f else 0.30f),
                    radius = (1.1f + (index % 3) * 0.35f).dp.toPx(), center = Offset(x, y))
            }
        }
    }
}
