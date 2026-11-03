package com.serie76.assistant.ui

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.*
import androidx.compose.material3.darkColorScheme
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import com.serie76.assistant.R

private val colors = lightColorScheme(
    primary = Color(0xFF73617F), onPrimary = Color.White,
    primaryContainer = Color(0xFFF0EAF7), onPrimaryContainer = Color(0xFF675479),
    secondary = Color(0xFF73617F), onSecondary = Color.White,
    secondaryContainer = Color(0xFFF0EAF7), onSecondaryContainer = Color(0xFF675479),
    tertiary = Color(0xFFBD7BFF), onTertiary = Color(0xFF211A2B),
    background = Color(0xFFFCFCFD), onBackground = Color(0xFF211A2B),
    surface = Color.White, onSurface = Color(0xFF211A2B),
    surfaceVariant = Color(0xFFF6F3F9), onSurfaceVariant = Color(0xFF62596C),
    outline = Color(0xFF94899E), outlineVariant = Color(0xFFE7E1EF),
    error = Color(0xFF9E2036), errorContainer = Color(0xFFFFE9ED), onErrorContainer = Color(0xFF6E1324),
)

private val darkColors = darkColorScheme(
    primary = Color(0xFFD0BDE2), onPrimary = Color(0xFF21182C),
    primaryContainer = Color(0xFF30263E), onPrimaryContainer = Color(0xFFE1D1F0),
    secondary = Color(0xFFD0BDE2), onSecondary = Color(0xFF21182C),
    secondaryContainer = Color(0xFF30263E), onSecondaryContainer = Color(0xFFE1D1F0),
    tertiary = Color(0xFFBD7BFF), onTertiary = Color(0xFF21182C),
    background = Color(0xFF101014), onBackground = Color(0xFFF4F0F8),
    surface = Color(0xFF1B1921), onSurface = Color(0xFFF4F0F8),
    surfaceVariant = Color(0xFF24212B), onSurfaceVariant = Color(0xFFBFB4CB),
    outline = Color(0xFF95869F), outlineVariant = Color(0xFF44394F),
    error = Color(0xFFFFB2BD), errorContainer = Color(0xFF42232D), onErrorContainer = Color(0xFFFFDCE2),
)

enum class AppearanceMode(val key: String, val label: String) {
    Light("light", "Light"), Dark("dark", "Dark"), System("system", "System");

    companion object {
        fun restored(key: String?, legacyDark: Boolean?): AppearanceMode =
            if (key != null) entries.firstOrNull { it.key == key } ?: System
            else when (legacyDark) { true -> Dark; false -> Light; null -> System }
    }
}

data class Appearance(val dark: Boolean, val mode: AppearanceMode, val setMode: (AppearanceMode) -> Unit)
val LocalAppearance = staticCompositionLocalOf { Appearance(false, AppearanceMode.System, {}) }

// Quiet washes rather than saturated purple controls, in both color schemes.
val SoftAccent: Brush
    @Composable get() = Brush.horizontalGradient(if (LocalAppearance.current.dark)
        listOf(Color(0xFF30273E), Color(0xFF433354)) else listOf(Color(0xFFF4ECFD), Color(0xFFE5DCF3)))

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
fun SeriesTheme(darkOverride: Boolean? = null, content: @Composable () -> Unit) {
    val context = LocalContext.current
    val systemDark = isSystemInDarkTheme()
    val preferences = remember(context) { context.getSharedPreferences("appearance", Context.MODE_PRIVATE) }
    var mode by remember(preferences) { mutableStateOf(AppearanceMode.restored(
        preferences.getString("mode", null),
        if (preferences.contains("dark")) preferences.getBoolean("dark", false) else null)) }
    val dark = darkOverride ?: when (mode) {
        AppearanceMode.Light -> false
        AppearanceMode.Dark -> true
        AppearanceMode.System -> systemDark
    }
    val view = LocalView.current
    val activity = remember(view.context) {
        generateSequence(view.context) { (it as? ContextWrapper)?.baseContext }.filterIsInstance<Activity>().firstOrNull()
    }
    SideEffect {
        activity?.let { WindowCompat.getInsetsController(it.window, view).apply {
            isAppearanceLightStatusBars = !dark
            isAppearanceLightNavigationBars = !dark
        } }
    }
    CompositionLocalProvider(LocalContentColor provides (if (dark) darkColors else colors).onBackground,
        LocalAppearance provides Appearance(dark, mode) { value ->
        mode = value
        preferences.edit().putString("mode", value.key).remove("dark").apply()
    }) {
    MaterialTheme(colorScheme = if (dark) darkColors else colors, typography = editorialType, shapes = Shapes(
        small = RoundedCornerShape(12.dp), medium = RoundedCornerShape(16.dp), large = RoundedCornerShape(24.dp)
    ), content = content)
    }
}
