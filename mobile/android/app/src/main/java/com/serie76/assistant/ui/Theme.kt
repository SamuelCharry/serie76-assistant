package com.serie76.assistant.ui

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

private val colors = lightColorScheme(
    primary = Color(0xFFBD7BFF), onPrimary = Color(0xFF211A2B),
    primaryContainer = Color(0xFFECE4F6), onPrimaryContainer = Color(0xFF4C315E),
    background = Color(0xFFFAFAFC), onBackground = Color(0xFF25232A),
    surface = Color.White, onSurface = Color(0xFF211A2B),
    surfaceVariant = Color(0xFFEFEEF4), onSurfaceVariant = Color(0xFF66616F),
    outline = Color(0xFF807887), outlineVariant = Color(0xFFDFDCE5),
    error = Color(0xFF9E2036), errorContainer = Color(0xFFFFE9ED), onErrorContainer = Color(0xFF6E1324),
)

@Composable
fun SeriesTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = colors, typography = Typography(), shapes = Shapes(
        small = RoundedCornerShape(12.dp), medium = RoundedCornerShape(20.dp), large = RoundedCornerShape(28.dp)
    ), content = content)
}
