package com.serie76.assistant

import android.content.Context
import android.content.ContentValues
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.compose.runtime.*
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModelStore
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import androidx.test.uiautomator.UiDevice
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.io.File
import java.net.ServerSocket
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

private val evidenceRun = "run-${System.currentTimeMillis()}"

/** P2-D: only these classes are selected for acceptance; no screenshot or real speech capture. */
abstract class P2DeviceHarness {
    @get:Rule val compose = createComposeRule()
    protected val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val store = ViewModelStore()
    protected lateinit var vm: AppViewModel
    private var developerWasEnabled = false
    private var developerWasPresent = false
    protected val developerPrefs get() = instrumentation.targetContext.getSharedPreferences("developer", Context.MODE_PRIVATE)

    @Before fun secureTestHost() {
        developerWasPresent = developerPrefs.contains("enabled")
        developerWasEnabled = developerPrefs.getBoolean("enabled", false)
        developerPrefs.edit().putBoolean("enabled", false).commit()
        compose.runOnUiThread {
            val activity = ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED).first() as ComponentActivity
            activity.window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
            activity.window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        }
    }

    protected fun own(model: androidx.lifecycle.ViewModel, name: String) { store.put(name, model) }

    protected fun mount(repository: ConversationRepository, api: retrofit2.Retrofit? = null) {
        compose.runOnUiThread { vm = AppViewModel(repository, SavedStateHandle()); own(vm, "chat") }
        compose.setContent { SeriesTheme(darkOverride = false) {
            CompositionLocalProvider(LocalAuthenticatedApi provides api) { SeriesApp(vm) }
        } }
        compose.waitUntil(10_000) { !vm.state.value.sessionsLoading }
    }

    protected fun awaitText(text: String, substring: Boolean = false, timeout: Long = 15_000) {
        compose.waitUntil(timeout) { compose.onAllNodesWithText(text, substring = substring).fetchSemanticsNodes().isNotEmpty() }
    }

    protected fun send(query: String) {
        compose.onNodeWithContentDescription("Message").performTextInput(query)
        compose.onNodeWithContentDescription("Send message").performClick()
    }

    protected fun assertNoInternals() {
        val forbidden = listOf("get_actuator", "search_actuators", "part_numbers", "motor_power_w", "tool_calls", "view.", "state.", "Traceback", "ValidationError")
        for (term in forbidden) {
            compose.onAllNodesWithText(term, substring = true, useUnmergedTree = true).assertCountEquals(0)
            compose.onAllNodesWithContentDescription(term, substring = true, useUnmergedTree = true).assertCountEquals(0)
        }
    }

    /** UiAutomator hierarchy XML, including secure windows; never clears FLAG_SECURE. */
    protected fun dump(name: String) {
        compose.waitForIdle()
        val directory = File(instrumentation.targetContext.cacheDir, "P2-D").apply { mkdirs() }
        val hierarchy = File(directory, "$name.xml")
        UiDevice.getInstance(instrumentation).dumpWindowHierarchy(hierarchy)
        val roots = compose.onAllNodes(isRoot(), useUnmergedTree = true)
        val semantics = File(directory, "$name-semantics.txt")
        semantics.writeText(
            roots.fetchSemanticsNodes().indices.joinToString("\n\n") { index ->
                "Window root $index\n" + roots[index].printToString()
            }
        )
        // Gradle uninstalls the APK after connected tests. Public Downloads survive that
        // cleanup; app-specific external files do not. API 35 is the acceptance target.
        check(Build.VERSION.SDK_INT >= 29) { "Evidence export requires Android 10 or later" }
        val resolver = instrumentation.targetContext.contentResolver
        for (file in listOf(hierarchy, semantics)) {
            val metadata = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, file.name)
                put(MediaStore.MediaColumns.MIME_TYPE, if (file.extension == "xml") "text/xml" else "text/plain")
                put(MediaStore.MediaColumns.RELATIVE_PATH, "${Environment.DIRECTORY_DOWNLOADS}/Series76-P2-D/$evidenceRun")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = requireNotNull(resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, metadata))
            requireNotNull(resolver.openOutputStream(uri)).use { output -> file.inputStream().use { it.copyTo(output) } }
            resolver.update(uri, ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }, null, null)
        }
    }

    @After fun releaseOwnedModelsAndPreferences() {
        compose.runOnUiThread { store.clear() }
        developerPrefs.edit().apply {
            if (developerWasPresent) putBoolean("enabled", developerWasEnabled) else remove("enabled")
        }.commit()
    }
}

/** Real HTTP/auth/SQL via emulator host. Only the two audited deterministic queries can be sent. */
class P2LiveDeviceAcceptanceTest : P2DeviceHarness() {
    private val created = mutableSetOf<String>()
    private val tokens = object : TokenStore {
        @Volatile private var token: String? = null
        override fun read() = token
        override fun write(token: String) { this.token = token }
        override fun clear() { token = null }
    }
    private val api by lazy { createRetrofit("http://10.0.2.2:8000/", tokens::read) }
    private val repository by lazy { ApiConversationRepository(api.create(ConversationApi::class.java)) }
    private val lookup = "What is the motor power of 761A00-11300000/A?"
    private val comparison = "Compare 761A00-11300000/A and 761B00-11300000/A"

    private fun login() {
        lateinit var auth: AuthViewModel
        compose.runOnUiThread { auth = AuthViewModel(api.create(AuthApi::class.java), tokens, api); own(auth, "auth") }
        val guarded = object : ConversationRepository by repository {
            override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>, removeFilters: List<String>, action: SuggestionAction?): ConversationResponse {
                check(query in setOf(lookup, comparison) && answers.isEmpty() && removeFilters.isEmpty() && action == null) {
                    "P2-D refuses a query outside the audited deterministic allowlist"
                }
                return repository.send(query, sessionId, answers, removeFilters, action).also { created.add(it.sessionId) }
            }
        }
        compose.setContent { SeriesTheme(darkOverride = false) {
            val state by auth.state.collectAsState()
            val user = state.user
            if (user == null) LoginScreen(state, auth::login, auth::restore)
            else {
                val chat = remember(user.id) { AppViewModel(guarded, SavedStateHandle()).also { vm = it; own(it, "chat") } }
                CompositionLocalProvider(LocalAccount provides AccountControls(user, state.busy, state.error, auth::logout),
                    LocalAuthenticatedApi provides api) { SeriesApp(chat) }
            }
        } }
        awaitText("Welcome back")
        dump("live-login") // Before entering credentials; bearer remains only in memory.
        compose.onNodeWithContentDescription("Sign in email").performTextInput("demo@series76.test")
        compose.onNodeWithContentDescription("Sign in password").performTextInput("Series76-Demo-1")
        compose.onNodeWithText("Sign in").performClick()
        compose.waitUntil(15_000) { auth.state.value.user != null }
        compose.waitForIdle()
        assertEquals("demo@series76.test", auth.state.value.user?.email)
        compose.waitUntil(15_000) { !vm.state.value.sessionsLoading }
        assertNull("Live conversation list failed", vm.state.value.sessionsError)
    }

    @Test fun demoLoginConversationsAndNewChat() {
        login()
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        awaitText("Conversations")
        compose.onNodeWithText("Conversations").assertIsDisplayed()
        if (vm.state.value.sessions.isEmpty()) compose.onNodeWithText("No conversations yet").assertIsDisplayed()
        else compose.onNodeWithText(vm.state.value.sessions.first().title).assertIsDisplayed()
        dump("live-conversations")
        compose.onNodeWithText("New chat").performClick()
        compose.onNodeWithContentDescription("Message").assertIsDisplayed()
        compose.onNodeWithContentDescription("Send message").assertIsNotEnabled()
        assertNull(vm.state.value.sessionId)
        assertTrue(vm.state.value.messages.isEmpty())
        dump("live-new-chat")
    }

    @Test fun keylessProductCardHasFiguresWithoutInternalNames() {
        login(); send(lookup)
        awaitText("Motor power")
        compose.onNodeWithText("15 W").assertIsDisplayed()
        compose.onNodeWithText("761A00-11300000/A", substring = false).assertIsDisplayed()
        assertNoInternals()
        compose.onNodeWithContentDescription("Debug details").assertDoesNotExist()
        dump("live-product-card")
    }

    @Test fun keylessTwoCodeComparisonHasTableWithoutInternalNames() {
        login(); send(comparison)
        awaitText("Field")
        compose.onNodeWithText("Field").performScrollTo().assertIsDisplayed()
        val table = compose.onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsProperties.CollectionInfo)).fetchSemanticsNodes()
        assertTrue("Two-model comparison requires a three-column table", table.any {
            it.config[SemanticsProperties.CollectionInfo].columnCount == 3
        })
        val result = vm.state.value.messages.last().comparison
        assertNotNull(result)
        assertEquals(listOf("761A00-11300000/A", "761B00-11300000/A"), result!!.models)
        assertTrue("Comparison must include numeric values", result.rows.any { row -> row.displayValues.any { it.any(Char::isDigit) } })
        val numericRow = result.rows.first { row -> row.displayValues.any { it.any(Char::isDigit) } }
        compose.onAllNodesWithText(numericRow.label).onLast().performScrollTo().assertIsDisplayed()
        numericRow.displayValues.forEach { value ->
            compose.onAllNodesWithText(value, substring = true).onLast().assertIsDisplayed()
        }
        assertNoInternals()
        dump("live-comparison")
    }

    @After fun removeOnlyTestCreatedSessions() = runBlocking {
        try { for (id in created) repository.deleteSession(id) }
        finally {
            if (tokens.read() != null) api.create(AuthApi::class.java).logout()
            tokens.clear()
        }
    }
}

/** Transport failures and timing use loopback MockWebServer; no provider or catalogue claims. */
class P2ControlledDeviceAcceptanceTest : P2DeviceHarness() {
    private var server: MockWebServer? = null
    private fun server(dispatch: (RecordedRequest) -> MockResponse): retrofit2.Retrofit {
        val instance = MockWebServer().also { server = it }
        instance.dispatcher = object : Dispatcher() { override fun dispatch(request: RecordedRequest) = dispatch(request) }
        instance.start()
        return createRetrofit(instance.url("/").toString())
    }
    private fun json(body: String) = MockResponse().setHeader("Content-Type", "application/json").setBody(body)
    private fun emptySessions() = json("""{"sessions":[]} """)

    @After fun closeServer() { server?.shutdown() }

    @Test fun closedPortShowsFriendlyErrorRetryAndResponsiveNavigation() {
        val port = ServerSocket(0).use { it.localPort }
        val api = createRetrofit("http://127.0.0.1:$port/")
        mount(ApiConversationRepository(api.create(ConversationApi::class.java)))
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        awaitText("Cannot reach the backend", substring = true)
        compose.onNodeWithText("Retry").assertIsEnabled().performClick()
        awaitText("Cannot reach the backend", substring = true)
        assertNoInternals()
        dump("controlled-history-error")
        compose.onNodeWithText("New chat").performClick()
        send("Transport failure fixture")
        awaitText("Cannot reach the backend", substring = true)
        compose.onNodeWithText("Retry").assertIsEnabled().performClick()
        awaitText("Cannot reach the backend", substring = true)
        compose.onNodeWithContentDescription("Message").performTextReplacement("Still responsive")
        compose.onNodeWithContentDescription("Message").assertTextEquals("Still responsive")
        dump("controlled-chat-error")
    }

    @Test fun fifteenSecondResponseKeepsVisibleLoadingUntilCompletion() {
        val calls = AtomicInteger()
        val api = server { request ->
            if (request.path!!.startsWith("/api/sessions")) emptySessions()
            else { calls.incrementAndGet(); json("""{"session_id":"slow","answer":"Delayed fixture completed","message_id":"slow-answer"}""")
                .setBodyDelay(15, TimeUnit.SECONDS) }
        }
        mount(ApiConversationRepository(api.create(ConversationApi::class.java)))
        val started = android.os.SystemClock.elapsedRealtime()
        send("Slow response fixture")
        awaitText("Searching the catalog\u2026")
        compose.onNodeWithText("Searching the catalog\u2026").assertIsDisplayed()
        compose.onNodeWithContentDescription("Send message").assertIsNotEnabled()
        dump("controlled-loading")
        // Real wall-clock wait: a virtual Compose clock cannot advance an HTTP body delay.
        compose.waitUntil(12_000) { android.os.SystemClock.elapsedRealtime() - started >= 10_000 }
        compose.onNodeWithText("Still working\u2026").assertIsDisplayed()
        awaitText("Delayed fixture completed", timeout = 15_000)
        assertTrue(android.os.SystemClock.elapsedRealtime() - started >= 15_000)
        assertEquals(1, calls.get())
        compose.onNodeWithText("Searching the catalog\u2026").assertDoesNotExist()
        compose.onNodeWithText("Still working\u2026").assertDoesNotExist()
        dump("controlled-loading-complete")
    }

    @Test fun sevenProfileTapsUnlockAnswerToolsParametersAndData() {
        val traceReads = AtomicInteger()
        val api = server { request -> when {
            request.path!!.startsWith("/api/sessions") -> emptySessions()
            request.path!!.startsWith("/api/messages/") -> {
                traceReads.incrementAndGet()
                json("""{"message_id":"debug-answer","session_id":"debug","tool_calls":[{"name":"get_actuator","parameters":{"part_numbers":["fixture-code"]},"data":{"fixture_result":"controlled data"}}]}""")
            }
            else -> json("""{"session_id":"debug","answer":"Controlled answer","message_id":"debug-answer"}""")
        } }
        mount(ApiConversationRepository(api.create(ConversationApi::class.java)), api)
        send("Debug fixture")
        awaitText("Controlled answer")
        compose.onNodeWithContentDescription("Debug details").assertDoesNotExist()
        assertEquals(0, traceReads.get())
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        compose.onNodeWithText("Profile").performTouchInput { repeat(6) { click(); advanceEventTime(50) } }
        assertFalse(developerPrefs.getBoolean("enabled", false))
        compose.onNodeWithText("Profile").performClick()
        compose.waitUntil(3000) { developerPrefs.getBoolean("enabled", false) }
        dump("controlled-developer-unlocked")
        compose.onNodeWithContentDescription("Close conversation history").performClick()
        compose.onNodeWithContentDescription("Debug details").performScrollTo().performClick()
        awaitText("Tools called", substring = true)
        compose.onNodeWithText("Tools called", substring = true).performClick()
        compose.onNodeWithText("[\n    \"get_actuator\"\n]").assertIsDisplayed()
        dump("controlled-debug-tools")
        compose.onNodeWithText("Validated parameters", substring = true).performScrollTo().performClick()
        compose.onNodeWithText("\"part_numbers\"", substring = true).performScrollTo().assertIsDisplayed()
        dump("controlled-debug-parameters")
        compose.onNodeWithText("Returned data", substring = true).performScrollTo().performClick()
        compose.onNodeWithText("controlled data", substring = true).performScrollTo().assertIsDisplayed()
        assertEquals(1, traceReads.get())
        dump("controlled-debug-data")
    }

    @Test fun deleteUndoRestoresConversationWithoutBackendDelete() {
        val deletes = AtomicInteger()
        val api = server { request ->
            if (request.method == "DELETE") { deletes.incrementAndGet(); MockResponse().setResponseCode(204) }
            else json("""{"sessions":[{"id":"undo","title":"Undo fixture conversation","updated_at":"2026-11-06T12:00:00Z"}]}""")
        }
        mount(ApiConversationRepository(api.create(ConversationApi::class.java)))
        compose.onNodeWithContentDescription("Open conversation history").performClick()
        compose.onNodeWithText("Undo fixture conversation").performTouchInput { longClick() }
        compose.onNodeWithText("Delete conversation?").assertIsDisplayed()
        dump("controlled-delete-confirmation")
        compose.onNodeWithText("Delete", substring = false).performClick()
        compose.onNodeWithText("Undo fixture conversation").assertDoesNotExist()
        // Undo is time limited: assert it, then click before performing any slow XML dump.
        compose.onNodeWithText("Undo").assertIsDisplayed().performClick()
        compose.onNodeWithText("Undo fixture conversation").assertIsDisplayed()
        val undoneAt = android.os.SystemClock.elapsedRealtime()
        compose.waitUntil(6500) { android.os.SystemClock.elapsedRealtime() - undoneAt >= 5500 }
        assertNull(vm.state.value.pendingDelete)
        assertEquals(0, deletes.get())
        dump("controlled-delete-undone")
    }

    @Test fun fakeVoiceTranscriptReachesComposerAndNeverAutoSends() {
        val sends = AtomicInteger()
        val api = server { request ->
            if (request.method == "POST") { sends.incrementAndGet(); MockResponse().setResponseCode(500) } else emptySessions()
        }
        mount(ApiConversationRepository(api.create(ConversationApi::class.java)))
        var callbacks: VoiceEvents? = null
        var released = false
        val fake = object : VoiceRecognizer {
            override fun start(events: VoiceEvents) { callbacks = events }
            override fun stop() {}
            override fun release() { released = true }
        }
        // Existing controller seam: real ChatScreen receives the same AppViewModel.draft callback.
        // Android microphone/permissions and the hardwired rememberVoiceInput factory remain manual.
        lateinit var controller: VoiceController
        compose.runOnUiThread {
            controller = VoiceController({ fake }, {}, vm::draft)
            controller.start(true, "")
            callbacks!!.partial("Partial spoken text")
        }
        compose.onNodeWithContentDescription("Message").assertTextEquals("Partial spoken text")
        compose.runOnUiThread { callbacks!!.final("Final spoken text for review") }
        compose.onNodeWithContentDescription("Message").assertTextEquals("Final spoken text for review")
        compose.onNodeWithContentDescription("Send message").assertIsEnabled()
        assertTrue(released)
        assertEquals(VoicePhase.IDLE, controller.state.phase)
        assertFalse(vm.state.value.sending)
        assertTrue(vm.state.value.messages.isEmpty())
        assertEquals(0, sends.get())
        dump("controlled-voice-review")
        compose.runOnUiThread { callbacks!!.final("Late callback must be ignored") }
        compose.onNodeWithContentDescription("Message").assertTextEquals("Final spoken text for review")
        assertEquals(0, sends.get())
    }
}
