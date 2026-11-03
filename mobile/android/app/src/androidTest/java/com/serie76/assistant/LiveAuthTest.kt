package com.serie76.assistant

import android.view.WindowManager
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.serie76.assistant.data.wireJson
import kotlinx.serialization.json.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.io.File

/** Opt-in real HTTP/SQL test; credentials arrive only through app-private test data. */
class LiveAuthTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun twoAccountsSeeOnlyTheirOwnSavedConversation() {
        val file = File(InstrumentationRegistry.getInstrumentation().targetContext.filesDir, "auth-verification.json")
        assumeTrue("Private live test configuration absent", file.isFile)
        val accounts = wireJson.parseToJsonElement(file.readText()).jsonArray
        try {
            // Capture only this instrumentation activity; production keeps FLAG_SECURE.
            compose.runOnUiThread { compose.activity.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
            compose.waitUntil(15000) { compose.onAllNodesWithText("Welcome back").fetchSemanticsNodes().isNotEmpty() }
            capture("live-login")
            accounts.forEachIndexed { index, value ->
                val item = value.jsonObject
                val email = item.getValue("email").jsonPrimitive.content
                val password = item.getValue("password").jsonPrimitive.content
                compose.onNodeWithContentDescription("Sign in email").performTextInput(email)
                compose.onNodeWithContentDescription("Sign in password").performTextInput(password)
                compose.onNodeWithText("Sign in").performClick()
                compose.waitUntil(15000) { compose.onAllNodesWithText("Hello").fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithContentDescription("Open conversation history").performClick()
                compose.waitUntil(15000) { compose.onAllNodesWithText("Verification account ${index + 1}").fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithText("Verification account ${2 - index}").assertDoesNotExist()
                compose.onNodeWithText("Verification account ${index + 1}").performClick()
                compose.waitUntil(15000) { compose.onAllNodesWithText("Saved verification answer ${index + 1}").fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithContentDescription("Open conversation history").performClick()
                compose.onNodeWithContentDescription("Open profile menu").performClick()
                compose.onAllNodesWithText(email, useUnmergedTree = true).onFirst().assertExists()
                capture("live-account-${index + 1}")
                compose.onNodeWithText("Sign out").performClick()
                compose.waitUntil(15000) { compose.onAllNodesWithText("Welcome back").fetchSemanticsNodes().isNotEmpty() }
            }
        } finally { file.delete() }
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        saveAuthScreenshot(name)
    }
}
