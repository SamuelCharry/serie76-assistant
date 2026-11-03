package com.serie76.assistant

import android.graphics.Bitmap
import android.content.ContentValues
import android.provider.MediaStore
import android.content.res.Configuration
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.SavedStateHandle
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import androidx.core.view.WindowCompat
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import java.io.File
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.Before
import androidx.activity.enableEdgeToEdge
import androidx.activity.SystemBarStyle

class ScreenTest {
    @get:Rule val compose = createComposeRule()

    @Before fun matchProductionWindow() {
        compose.runOnUiThread {
            val activity = ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED).first() as androidx.activity.ComponentActivity
            activity.enableEdgeToEdge(
                statusBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
                navigationBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            )
            activity.window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        }
    }

    private val session = Session("test-session", "110 V actuator selection", "2026-11-03T12:00:00Z", "Compare published torque and motor power.")
    private val product = Product(
        partNumber = "761A00-11300000/A", enclosure = "weatherproof", voltage = JsonPrimitive(110), current = "AC", phases = 1,
        dataStatus = "reported", serviceLayout = "mixed",
        measurements = mapOf("motor_power_w" to JsonPrimitive(15), "on_off_torque_nm" to JsonPrimitive(80), "modulating_torque_nm" to JsonPrimitive(65)),
        fieldStatus = mapOf("motor_power_w" to "reported", "on_off_torque_nm" to "reported", "modulating_torque_nm" to "reported"),
        source = ProductSource("series_76_electric_data.pdf", 1, "p1_t1"),
    )

    @Test fun conversationsAndNewChat() {
        val repo = object : ConversationRepository {
            override suspend fun sessions(offset: Int) = SessionsPage(listOf(session,
                session.copy(id = "second", title = "Compare modulating models", preview = "Review published torque and duty cycle for modulating service."),
                session.copy(id = "third", title = "24 V power requirements", preview = "Look up published data for a low-voltage application.")))
            override suspend fun messages(sessionId: String, before: Long?) = MessagesPage(sessionId, session.title,
                listOf(Message("saved-user", "user", "Look up 761A00-11300000/A"), Message("saved-answer", "assistant", "Saved response", listOf(product))))
            override suspend fun send(query: String, sessionId: String?) = ConversationResponse("test-session", "Published data", "answer")
        }
        compose.setContent { SeriesTheme { SeriesApp(androidx.lifecycle.viewmodel.compose.viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST") override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = AppViewModel(repo, SavedStateHandle()) as T
        })) } }
        compose.onNodeWithText("Hello.\nHow can I help?").assertIsDisplayed()
        screenshot("chat-home")
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        compose.onNodeWithText("110 V actuator selection").assertIsDisplayed()
        screenshot("conversations")
        compose.runOnUiThread {
            val activity = ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED).first() as androidx.activity.ComponentActivity
            activity.onBackPressedDispatcher.onBackPressed()
        }
        compose.onNodeWithText("Hello.\nHow can I help?").assertIsDisplayed()
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        compose.onNodeWithText("110 V actuator selection").performClick()
        compose.onNodeWithText("Saved response").assertExists()
        screenshot("chat-resumed")
        compose.onNodeWithContentDescription("New conversation").performClick()
        compose.onNodeWithText("Look up a part").performClick()
        compose.onNodeWithContentDescription("Ask Series 76").assertTextContains("Look up the actuator", substring = true)
        compose.onNodeWithContentDescription("Ask Series 76").performTextClearance()
        compose.onNodeWithContentDescription("Ask Series 76").performTextInput("Look up 761A00-11300000/A")
        screenshot("chat-keyboard")
        compose.onNodeWithContentDescription("Send message").performClick()
        compose.onNodeWithText("Published data").assertExists()
        screenshot("chat-sent")
    }

    @Test fun emptyAndErrorAreActionable() {
        var retry = false
        compose.setContent { SeriesTheme { Box(Modifier.statusBarsPadding()) { ConversationsScreen(AppState(sessionsError = "Cannot reach the backend."), {}, {}, { retry = true }, {}) } } }
        compose.onNodeWithText("Cannot reach the backend.").assertExists()
        compose.onNodeWithText("Try again").performClick()
        assertTrue(retry)
        screenshot("backend-error")
    }

    @Test fun emptyConversationsExplainsAction() {
        compose.setContent { SeriesTheme { Box(Modifier.statusBarsPadding()) { ConversationsScreen(AppState(), {}, {}, {}, {}) } } }
        compose.onNodeWithText("No conversations yet").assertExists()
        compose.onNodeWithText("New chat").assertIsEnabled()
        screenshot("conversations-empty")
    }

    @Test fun developerShowsParametersAndReturnedData() {
        val parameters = buildJsonObject { putJsonArray("part_numbers") { add(product.partNumber) } }
        val returned = buildJsonObject { put("status", "ok"); put("source", "PostgreSQL test fixture") }
        val state = AppState(screen = "debug", messages = listOf(Message("answer", "assistant", "Published catalogue data is shown below.")))
        compose.setContent { SeriesTheme { DeveloperScreen(state, {}, {}, { id ->
            DebugResponse(id, "test-session", listOf(ToolCall("get_actuator", parameters, returned)))
        }) } }
        compose.onNodeWithText("get_actuator").assertExists()
        compose.onNodeWithText("Parameters").assertExists()
        compose.onNodeWithText("Returned data").assertExists()
        screenshot("developer-debug")
    }

    @Test fun productKeepsCompleteCodeAndServiceLabelsAtLargeText() {
        compose.setContent {
            val density = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(density.density, 1.3f)) {
                SeriesTheme { ChatScreen(AppState(screen = "chat", title = "Published specifications",
                    messages = listOf(Message("answer", "assistant", "Published catalogue data is shown below.", listOf(product)))), {}, {}, {}, {}, {}, {}, {}) }
            }
        }
        compose.onNodeWithText("761A00-11300000/A").assertExists()
        compose.onNodeWithText("On/Off torque").assertExists()
        compose.onNodeWithText("Modulating torque").assertExists()
        screenshot("product-font130")
    }

    @Test fun comparisonScrollKeepsAttributeLabels() {
        val other = product.copy(partNumber = "761B00-11300000/A", measurements = product.measurements +
            mapOf("on_off_torque_nm" to JsonPrimitive(100), "modulating_torque_nm" to JsonPrimitive(70)))
        compose.setContent { SeriesTheme { ChatScreen(AppState(screen = "chat", title = "Compare actuators",
            messages = listOf(Message("comparison", "assistant", "Compare the published specifications below.", listOf(product, other)))), {}, {}, {}, {}, {}, {}, {}) } }
        compose.onNodeWithText("Swipe across to compare. Attribute labels stay in place.").assertExists()
        compose.onNodeWithText("On/Off torque (Nm)").assertExists()
        compose.onNodeWithContentDescription("761A00-11300000/A, On/Off torque: 80 Nm").assertExists()
        screenshot("comparison")
        compose.onAllNodes(hasScrollAction()).fetchSemanticsNodes().let { assertTrue(it.isNotEmpty()) }
    }

    private fun screenshot(name: String) {
        compose.runOnUiThread {
            // Empty Compose test host: match the production activity's explicit light bars.
            ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED).firstOrNull()?.let { activity ->
                WindowCompat.getInsetsController(activity.window, activity.window.decorView).apply {
                    isAppearanceLightStatusBars = true
                    isAppearanceLightNavigationBars = true
                }
            }
        }
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        // System bar appearance is applied by WindowManager on the next frame.
        android.os.SystemClock.sleep(100)
        val resolver = instrumentation.targetContext.contentResolver
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
            put(MediaStore.Images.Media.MIME_TYPE, "image/png")
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/Series76Verification/gemini-v2-final")
            put(MediaStore.Images.Media.IS_PENDING, 1)
        }
        val uri = requireNotNull(resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values))
        resolver.openOutputStream(uri)!!.use {
            requireNotNull(instrumentation.uiAutomation.takeScreenshot()).compress(Bitmap.CompressFormat.PNG, 100, it)
        }
        values.clear(); values.put(MediaStore.Images.Media.IS_PENDING, 0)
        resolver.update(uri, values, null, null)
    }
}
