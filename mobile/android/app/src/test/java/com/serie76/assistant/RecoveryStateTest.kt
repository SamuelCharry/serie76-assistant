package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.AppViewModel
import java.io.IOException
import java.net.ConnectException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response

@OptIn(ExperimentalCoroutinesApi::class)
class RecoveryStateTest {
    private val main = StandardTestDispatcher()
    @Before fun setup() { Dispatchers.setMain(main) }
    @After fun teardown() { Dispatchers.resetMain() }

    private fun http(status: Int, code: String = "private") = HttpException(Response.error<Unit>(status,
        """{"error_code":"$code","detail":"private internal trace"}""".toResponseBody("application/json".toMediaType())))

    private class Repository : ConversationRepository {
        var error: Exception? = null
        var sendFailure: Exception? = null
        val offsets = mutableListOf<Int>()
        val cursors = mutableListOf<Long?>()
        val requests = mutableListOf<ConversationRequest>()
        override suspend fun sessions(offset: Int): SessionsPage {
            offsets += offset
            error?.let { throw it }
            return SessionsPage(listOf(Session("s$offset", "Saved", "")), limit = 1)
        }
        override suspend fun messages(sessionId: String, before: Long?): MessagesPage {
            cursors += before
            error?.let { throw it }
            return MessagesPage(sessionId, "Saved", listOf(Message(if (before == null) "new" else "old", "assistant", "Saved")),
                hasMore = before == null, nextBefore = if (before == null) 10 else null)
        }
        override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>, removeFilters: List<String>, action: SuggestionAction?): ConversationResponse {
            requests += ConversationRequest(query, sessionId, answers, removeFilters, action)
            sendFailure?.let { throw it }
            return ConversationResponse(sessionId ?: "s", "Answer", "a")
        }
        override suspend fun deleteSession(sessionId: String) = Unit
    }

    @Test fun `transport allows the backend deadline and does not automatically retry writes`() {
        val client = conversationHttpClient()
        assertEquals(10_000, client.connectTimeoutMillis)
        assertEquals(70_000, client.readTimeoutMillis)
        assertEquals(75_000, client.callTimeoutMillis)
        assertTrue(client.readTimeoutMillis > 60_000)
        assertTrue(client.callTimeoutMillis > client.readTimeoutMillis)
        assertFalse(client.retryOnConnectionFailure)
        assertFalse(client.followRedirects)
    }

    @Test fun `unknown HTTP status has a safe fallback and classification does not consume error codes`() {
        assertEquals("The assistant is unavailable. Check that the backend is running and configured.", failureMessage(http(418)))
        val config = http(503, "not_configured")
        assertFalse(requiresReconciliation(config))
        repeat(2) { assertEquals("The assistant is not configured on the server.", failureMessage(config)) }
        assertFalse(requiresReconciliation(http(402, "budget_exhausted")))
        assertFalse(requiresReconciliation(ConnectException("private")))
        assertTrue(requiresReconciliation(http(409, "busy")))
    }

    @Test fun `existing session ambiguous send reloads before an explicit retry and keeps exact draft`() = runTest(main) {
        val repo = Repository(); val saved = SavedStateHandle()
        val vm = AppViewModel(repo, saved)
        vm.open(Session("s", "Saved", "")); advanceUntilIdle()
        repo.sendFailure = IOException("private")
        vm.draft("  Keep me  "); vm.send(); advanceUntilIdle()
        assertTrue(vm.state.value.needsReconcile)
        assertEquals("  Keep me  ", saved.get<String>("draft"))
        vm.retrySend(); advanceUntilIdle()
        assertEquals(1, repo.requests.size)
        assertFalse(vm.state.value.needsReconcile)
        assertEquals("  Keep me  ", vm.state.value.draft)
        repo.sendFailure = null
        vm.retrySend(); advanceUntilIdle()
        assertEquals(2, repo.requests.size)
        assertEquals(repo.requests[0], repo.requests[1])
        assertNull(vm.state.value.sendError)
    }

    @Test fun `explicit rejection permits retry of a structured action without losing its arguments`() = runTest(main) {
        val repo = Repository(); val vm = AppViewModel(repo, SavedStateHandle()); advanceUntilIdle()
        repo.sendFailure = http(402, "budget_exhausted")
        vm.sendSuggestion(Suggestion("More", SuggestionAction("next_page"))); advanceUntilIdle()
        assertFalse(vm.state.value.needsReconcile)
        assertTrue(vm.state.value.canSend)
        repo.sendFailure = null
        vm.retrySend(); advanceUntilIdle()
        assertEquals(2, repo.requests.size)
        assertEquals(repo.requests[0], repo.requests[1])
        assertEquals("next_page", repo.requests[1].action?.type)
    }

    @Test fun `editing failed text makes retry submit the edited text without stale action`() = runTest(main) {
        val repo = Repository(); val vm = AppViewModel(repo, SavedStateHandle()); advanceUntilIdle()
        repo.sendFailure = http(503, "not_configured")
        vm.sendSuggestion(Suggestion("More", SuggestionAction("next_page"))); advanceUntilIdle()
        vm.draft("Different question")
        repo.sendFailure = null
        vm.retrySend(); advanceUntilIdle()
        assertEquals("Different question", repo.requests.last().query)
        assertNull(repo.requests.last().action)
    }

    @Test fun `retry of failed later session page keeps offset visible rows and draft`() = runTest(main) {
        val repo = Repository(); val vm = AppViewModel(repo, SavedStateHandle()); advanceUntilIdle()
        vm.draft("Unsent")
        repo.error = http(500)
        vm.refreshSessions(more = true); advanceUntilIdle()
        assertEquals(listOf("s0"), vm.state.value.sessions.map { it.id })
        assertNotNull(vm.state.value.sessionsError)
        repo.error = null
        vm.retrySessions(); advanceUntilIdle()
        assertEquals(listOf(0, 1, 1), repo.offsets)
        assertEquals(listOf("s0", "s1"), vm.state.value.sessions.map { it.id })
        assertEquals("Unsent", vm.state.value.draft)
    }

    @Test fun `retry of failed earlier history page keeps cursor visible messages and draft`() = runTest(main) {
        val repo = Repository(); val vm = AppViewModel(repo, SavedStateHandle())
        vm.open(Session("s", "Saved", "")); advanceUntilIdle()
        vm.draft("Unsent")
        repo.error = http(500)
        vm.loadHistory(older = true); advanceUntilIdle()
        assertEquals(listOf("new"), vm.state.value.messages.map { it.id })
        assertNotNull(vm.state.value.historyError)
        repo.error = null
        vm.retryHistory(); advanceUntilIdle()
        assertEquals(listOf(null, 10L, 10L), repo.cursors)
        assertEquals(listOf("old", "new"), vm.state.value.messages.map { it.id })
        assertEquals("Unsent", vm.state.value.draft)
    }
}
