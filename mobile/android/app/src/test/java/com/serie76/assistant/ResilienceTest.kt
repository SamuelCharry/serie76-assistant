package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModelStore
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.AppViewModel
import java.net.UnknownHostException
import java.net.InetAddress
import java.util.concurrent.TimeUnit
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.*
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import okhttp3.mockwebserver.SocketPolicy
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

/** Real Retrofit/OkHttp responses exercise the same error mapping for all three operations. */
@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(Parameterized::class)
class ResilienceTest(private val operation: String, private val scenario: String) {
    companion object {
        @JvmStatic @Parameterized.Parameters(name = "{0}: {1}")
        fun cases(): List<Array<String>> = listOf("send", "sessions", "history").flatMap { operation ->
            listOf("delay15", "500", "503-config", "503-db", "402", "502", "504", "409",
                "timeout", "offline", "malformed", "empty", "missing", "null", "204").map { arrayOf(operation, it) }
        }
    }

    private val main = StandardTestDispatcher()
    private val store = ViewModelStore()
    @Before fun setup() { Dispatchers.setMain(main) }
    @After fun teardown() { store.clear(); Dispatchers.resetMain() }

    private fun target(path: String) = when (operation) {
        "send" -> path.substringBefore('?') == "/api/conversation"
        "sessions" -> path.startsWith("/api/sessions?")
        else -> path.startsWith("/api/sessions/s/messages")
    }

    private fun success(path: String) = MockResponse().setHeader("Content-Type", "application/json").setBody(when {
        path == "/api/conversation" -> """{"session_id":"s","message_id":"answer","answer":"Published data"}"""
        path.contains("/messages") -> """{"session_id":"s","title":"Saved","messages":[{"id":"old","role":"assistant","content":"Saved answer"}]}"""
        else -> """{"sessions":[{"id":"s","title":"Saved","updated_at":"2026-11-05T00:00:00Z"}]}"""
    })

    private fun response(path: String): MockResponse = when (scenario) {
        "delay15" -> success(path).setBodyDelay(15, TimeUnit.SECONDS)
        "timeout" -> MockResponse().setSocketPolicy(SocketPolicy.NO_RESPONSE)
        "malformed" -> MockResponse().setBody("{private internal trace")
        "empty" -> MockResponse().setBody("")
        "missing" -> MockResponse().setBody("{}")
        "null" -> MockResponse().setBody("null")
        "204" -> MockResponse().setResponseCode(204)
        else -> MockResponse().setResponseCode(scenario.substringBefore('-').toInt()).setBody(
            """{"error_code":"${when(scenario) {
                "503-config" -> "not_configured"
                "503-db" -> "database_unavailable"
                "402" -> "budget_exhausted"
                "409" -> "busy"
                else -> "provider_failure"
            }}","detail":"private internal trace"}"""
        )
    }

    private fun expectedMessage() = when (scenario) {
        "500" -> "The server could not complete the request. Please try again shortly."
        "503-config" -> "The assistant is not configured on the server."
        "503-db" -> "Saved conversations are temporarily unavailable. Please try again shortly."
        "402" -> "The assistant's service budget has run out. Please contact the administrator and try again later."
        "502" -> "The assistant's service could not respond. Please try again shortly."
        "504" -> "The assistant's service took too long to respond. Please try again shortly."
        "409" -> "A response is already being prepared. Reload the conversation before sending again."
        "timeout" -> "The server took too long to respond. Please try again shortly."
        "offline" -> "Cannot reach the backend. Check your connection and the backend address."
        else -> "The response could not be loaded. Please try again."
    }

    private suspend fun settle(vm: AppViewModel) = withContext(Dispatchers.Default) {
        withTimeout(22_000) {
            while (vm.state.value.let { it.sending || it.sessionsLoading || it.historyLoading }) delay(10)
        }
    }

    @Test fun `loading draft friendly result and explicit recovery`() = runTest(main) {
        MockWebServer().use { server ->
            val failing = AtomicBoolean(true)
            val release = CountDownLatch(1)
            val caller = Thread.currentThread()
            val networkOnCaller = AtomicBoolean(false)
            server.dispatcher = object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val path = request.path!!
                    return if (target(path) && failing.get()) response(path) else success(path)
                }
            }
            // Pin one route: after a failed connection OkHttp can try another localhost
            // address (IPv4/IPv6), on which this single-address test server is not listening.
            server.start(InetAddress.getByName("127.0.0.1"), 0)
            val client = conversationHttpClient().newBuilder().apply {
                addInterceptor { chain ->
                    if (Thread.currentThread() === caller) networkOnCaller.set(true)
                    if (target(chain.request().url.encodedPath + "?" + chain.request().url.encodedQuery.orEmpty()) && failing.get()) {
                        check(release.await(5, TimeUnit.SECONDS))
                        if (scenario == "offline") throw UnknownHostException("private internal host")
                        // Only the failing request gets a short deadline. NO_RESPONSE cannot race
                        // a delayed successful body, and setup/recovery retain production timeouts.
                        if (scenario == "timeout") return@addInterceptor chain
                            .withReadTimeout(150, TimeUnit.MILLISECONDS).proceed(chain.request())
                    }
                    chain.proceed(chain.request())
                }
            }.build()
            val serverUrl = server.url("/").newBuilder().host("127.0.0.1").build()
            val api = Retrofit.Builder().baseUrl(serverUrl).client(client)
                .addConverterFactory(wireJson.asConverterFactory("application/json".toMediaType())).build()
                .create(ConversationApi::class.java)
            val saved = SavedStateHandle(mapOf("draft" to "  Keep my exact text  "))
            val vm = AppViewModel(ApiConversationRepository(api), saved)
            store.put("vm", vm)
            runCurrent()
            if (operation != "sessions") {
                settle(vm)
                if (operation == "history") {
                    vm.open(Session("s", "Saved", ""))
                    vm.draft("  Keep my exact text  ")
                } else vm.send()
                runCurrent()
            }
            assertTrue(vm.state.value.let { when(operation) {
                "send" -> it.sending
                "sessions" -> it.sessionsLoading
                else -> it.historyLoading
            } })
            if (operation != "sessions") assertFalse(vm.state.value.canSend)
            assertEquals("  Keep my exact text  ", vm.state.value.draft)
            release.countDown()
            if (scenario == "delay15") {
                // Real wall-clock HTTP delay: main remains available while the socket waits.
                withContext(Dispatchers.Default) { delay(100) }
                if (operation == "send") {
                    vm.draft("Late callback cannot erase disabled composer")
                    assertEquals("  Keep my exact text  ", vm.state.value.draft)
                } else {
                    vm.draft("Still editable")
                    assertEquals("Still editable", vm.state.value.draft)
                    vm.draft("  Keep my exact text  ")
                }
                assertTrue(vm.state.value.let { it.sending || it.sessionsLoading || it.historyLoading })
            }
            settle(vm)
            assertFalse("HTTP must not execute on the ViewModel caller", networkOnCaller.get())
            val error = vm.state.value.let { when(operation) {
                "send" -> it.sendError
                "sessions" -> it.sessionsError
                else -> it.historyError
            } }
            if (scenario == "delay15") {
                assertNull(error)
                assertTrue(vm.state.value.canSend)
                if (operation == "send") assertEquals("", saved.get<String>("draft"))
                else assertEquals("  Keep my exact text  ", saved.get<String>("draft"))
            } else {
                assertEquals(expectedMessage(), error)
                assertEquals("  Keep my exact text  ", vm.state.value.draft)
                assertEquals(vm.state.value.draft, saved.get<String>("draft"))
                failing.set(false)
                when(operation) {
                    "send" -> vm.retrySend()
                    "sessions" -> vm.retrySessions()
                    else -> vm.retryHistory()
                }
                runCurrent(); settle(vm)
                assertNull(vm.state.value.sendError)
                assertNull(vm.state.value.sessionsError)
                assertNull(vm.state.value.historyError)
                assertTrue(vm.state.value.canSend)
                if (operation == "send") assertEquals("Published data", vm.state.value.messages.last().content)
                else assertEquals("  Keep my exact text  ", vm.state.value.draft)
            }
        }
    }
}
