package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AppViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun teardown() { Dispatchers.resetMain() }

    private class Repository : ConversationRepository {
        val requests = mutableListOf<Pair<String, String?>>()
        var failure = false
        var waitForSend: CompletableDeferred<Unit>? = null
        var history = listOf(Message("persisted-user", "user", "Initial query"), Message("persisted-answer", "assistant", "Initial answer"))
        override suspend fun sessions(offset: Int) = SessionsPage(listOf(Session("saved-session", "Saved", "2026-11-03T12:00:00Z")))
        override suspend fun messages(sessionId: String, before: Long?) = MessagesPage(sessionId, "Saved", history)
        override suspend fun send(query: String, sessionId: String?): ConversationResponse {
            requests += query to sessionId
            waitForSend?.await()
            if (failure) throw IOException("private internal URL must not be exposed")
            return ConversationResponse(sessionId ?: "new-session", "Published data", "answer-${requests.size}")
        }
    }

    @Test fun `chat first startup and history dismissal preserve draft without sending`() = runTest(dispatcher) {
        val repo = Repository(); val saved = SavedStateHandle(); val vm = AppViewModel(repo, saved)
        advanceUntilIdle()
        assertEquals("chat", vm.state.value.screen)
        vm.draft("Keep my draft")
        vm.showConversations(); advanceUntilIdle()
        assertEquals("sessions", vm.state.value.screen)
        vm.dismissConversations()
        assertEquals("chat", vm.state.value.screen)
        assertEquals("Keep my draft", vm.state.value.draft)
        assertEquals("Keep my draft", saved.get<String>("draft"))
        assertTrue(repo.requests.isEmpty())
    }

    @Test fun `first turn starts a session and next turn keeps it`() = runTest(dispatcher) {
        val repo = Repository(); val vm = AppViewModel(repo, SavedStateHandle())
        advanceUntilIdle(); vm.newConversation(); vm.draft("First"); vm.send(); advanceUntilIdle()
        assertEquals("new-session", vm.state.value.sessionId)
        vm.draft("And its power?"); vm.send(); advanceUntilIdle()
        assertEquals(listOf("First" to null, "And its power?" to "new-session"), repo.requests)
    }

    @Test fun `pending request blocks duplicate submit and opening another session`() = runTest(dispatcher) {
        val repo = Repository(); repo.waitForSend = CompletableDeferred()
        val vm = AppViewModel(repo, SavedStateHandle()); advanceUntilIdle()
        vm.newConversation(); vm.draft("Question"); vm.send(); vm.send(); runCurrent()
        assertEquals(1, repo.requests.size)
        vm.open(Session("other", "Other", "")); assertNull(vm.state.value.sessionId)
        vm.back(); repo.waitForSend!!.complete(Unit); advanceUntilIdle()
        assertEquals("sessions", vm.state.value.screen)
        assertEquals("new-session", vm.state.value.sessionId)
    }

    @Test fun `failure preserves draft and requires reconciliation before resending`() = runTest(dispatcher) {
        val repo = Repository(); val saved = SavedStateHandle(); val vm = AppViewModel(repo, saved)
        advanceUntilIdle(); vm.open(Session("saved-session", "Saved", "")); advanceUntilIdle()
        repo.failure = true; vm.draft("Keep this question"); vm.send(); advanceUntilIdle()
        assertEquals("Keep this question", vm.state.value.draft)
        assertTrue(vm.state.value.needsReconcile)
        assertFalse(vm.state.value.sendError!!.contains("private"))
        vm.send(); advanceUntilIdle(); assertEquals(1, repo.requests.size)
        vm.reconcile(); advanceUntilIdle(); assertFalse(vm.state.value.needsReconcile)
    }

    @Test fun `restoration reloads persisted history and keeps session and draft`() = runTest(dispatcher) {
        val saved = SavedStateHandle(mapOf("sessionId" to "saved-session", "screen" to "chat", "draft" to "Unsent", "inFlight" to true))
        val vm = AppViewModel(Repository(), saved); advanceUntilIdle()
        assertEquals("saved-session", vm.state.value.sessionId)
        assertEquals("Unsent", vm.state.value.draft)
        assertEquals(2, vm.state.value.messages.size)
        assertFalse(vm.state.value.needsReconcile)
    }
}
