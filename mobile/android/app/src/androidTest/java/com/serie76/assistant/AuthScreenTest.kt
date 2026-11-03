package com.serie76.assistant

import android.graphics.Bitmap
import android.content.ContentValues
import android.provider.MediaStore
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import com.serie76.assistant.data.Account
import com.serie76.assistant.ui.*
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

internal fun saveAuthScreenshot(name: String) {
    val instrumentation = InstrumentationRegistry.getInstrumentation()
    val resolver = instrumentation.targetContext.contentResolver
    val values = ContentValues().apply {
        put(MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
        put(MediaStore.Images.Media.MIME_TYPE, "image/png")
        put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/Series76Verification/auth-v7-round-1")
    }
    val uri = requireNotNull(resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values))
    instrumentation.waitForIdleSync()
    Thread.sleep(250) // Popup windows render on Android's clock, independently of Compose idleness.
    val image = instrumentation.uiAutomation.takeScreenshot()
    resolver.openOutputStream(uri)!!.use { image.compress(Bitmap.CompressFormat.PNG, 100, it) }
    image.recycle()
}

class AuthScreenTest {
    @get:Rule val compose = createComposeRule()

    @Test fun loginHasMaskedPasswordAndClearsItAfterSubmit() {
        val state = mutableStateOf(AuthState(checking = false))
        var submitted: Pair<String, String>? = null
        compose.setContent { SeriesTheme(darkOverride = false) { LoginScreen(state.value, { email, password ->
            submitted = email to password
            state.value = AuthState(checking = false, error = "Email or password is incorrect.")
        }, {}) } }
        compose.onNodeWithText("Sign in").assertIsNotEnabled()
        capture("login-light")
        compose.onNodeWithContentDescription("Sign in email").performTextInput("user@example.test")
        compose.onNodeWithContentDescription("Sign in password").performTextInput("synthetic password")
        compose.onNodeWithContentDescription("Sign in password").assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Password))
        compose.onNodeWithText("Sign in").performClick()
        compose.onNodeWithText("Email or password is incorrect.").assertIsDisplayed()
        assertEquals("user@example.test" to "synthetic password", submitted)
        assertEquals("", compose.onNodeWithContentDescription("Sign in password").fetchSemanticsNode().config[SemanticsProperties.EditableText].text)
    }

    @Test fun authenticatedProfileUsesServerIdentityAndSignOut() {
        var signOut = false
        compose.setContent { SeriesTheme(darkOverride = true) {
            CompositionLocalProvider(LocalAccount provides AccountControls(Account("fixture", "user@example.test", "Example user"), false, null, { signOut = true })) {
                Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(top = 400.dp, start = 20.dp, end = 20.dp)) { ProfileMenu() }
            }
        } }
        compose.onNodeWithContentDescription("Open profile menu").performClick()
        compose.onNodeWithText("Signed in").assertIsDisplayed()
        compose.onNodeWithText("Edit profile").assertDoesNotExist()
        compose.onNodeWithText("System").assertIsDisplayed()
        capture("account-dark")
        compose.onNodeWithText("Sign out").performClick()
        assertTrue(signOut)
    }

    @Test fun loginRemainsUsableInDarkAndLargeFont() {
        val dark = mutableStateOf(true)
        compose.setContent {
            val density = androidx.compose.ui.platform.LocalDensity.current
            CompositionLocalProvider(androidx.compose.ui.platform.LocalDensity provides androidx.compose.ui.unit.Density(density.density, 1.3f)) {
                SeriesTheme(darkOverride = dark.value) { LoginScreen(AuthState(checking = false), { _, _ -> }, {}) }
            }
        }
        compose.onNodeWithContentDescription("Sign in email").assertIsDisplayed()
        compose.onNodeWithContentDescription("Sign in password").assertIsDisplayed()
        capture("login-dark-font130")
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        saveAuthScreenshot(name)
    }
}
