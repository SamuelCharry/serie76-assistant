package com.serie76.assistant.ui

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import com.serie76.assistant.R

private val colors = lightColorScheme(
    primary = Color(0xFF412C64), onPrimary = Color.White,
    primaryContainer = Color(0xFFEEE3FC), onPrimaryContainer = Color(0xFF412C64),
    secondary = Color(0xFF412C64), onSecondary = Color.White,
    secondaryContainer = Color(0xFFEEE3FC), onSecondaryContainer = Color(0xFF412C64),
    tertiary = Color(0xFFBD7BFF), onTertiary = Color(0xFF211A2B),
    background = Color(0xFFFCFCFD), onBackground = Color(0xFF211A2B),
    surface = Color.White, onSurface = Color(0xFF211A2B),
    surfaceVariant = Color(0xFFF6F3F9), onSurfaceVariant = Color(0xFF62596C),
    outline = Color(0xFF8A7E98), outlineVariant = Color(0xFFD0ACE5),
    error = Color(0xFF9E2036), errorContainer = Color(0xFFFFE9ED), onErrorContainer = Color(0xFF6E1324),
)

private val typeface = FontFamily(
    Font(R.font.rethink_regular, FontWeight.Normal),
    Font(R.font.rethink_medium, FontWeight.Medium),
    Font(R.font.rethink_semibold, FontWeight.SemiBold),
)

private val editorialType = Typography(
    displaySmall = TextStyle(fontFamily = typeface, fontWeight = FontWeight.SemiBold, fontSize = 38.sp, lineHeight = 42.sp, letterSpacing = (-0.8).sp),
    headlineLarge = TextStyle(fontFamily = typeface, fontWeight = FontWeight.SemiBold, fontSize = 32.sp, lineHeight = 38.sp, letterSpacing = (-0.5).sp),
    headlineSmall = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 24.sp, lineHeight = 30.sp),
    titleLarge = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 22.sp, lineHeight = 28.sp),
    titleMedium = TextStyle(fontFamily = typeface, fontWeight = FontWeight.SemiBold, fontSize = 18.sp, lineHeight = 24.sp),
    titleSmall = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 15.sp, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Normal, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Normal, fontSize = 14.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Normal, fontSize = 12.sp, lineHeight = 18.sp),
    labelLarge = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 12.sp, lineHeight = 16.sp),
    labelSmall = TextStyle(fontFamily = typeface, fontWeight = FontWeight.Medium, fontSize = 11.sp, lineHeight = 16.sp),
)

@Composable
fun SeriesTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = colors, typography = editorialType, shapes = Shapes(
        small = RoundedCornerShape(12.dp), medium = RoundedCornerShape(16.dp), large = RoundedCornerShape(24.dp)
    ), content = content)
}
