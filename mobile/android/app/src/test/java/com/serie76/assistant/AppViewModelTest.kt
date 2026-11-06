package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModelStore
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
        override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>, removeFilters: List<String>, action: SuggestionAction?): ConversationResponse {
            requests += query to sessionId
            waitForSend?.await()
            if (failure) throw IOException("private internal URL must not be exposed")
            return ConversationResponse(sessionId ?: "new-session", "Published data", "answer-${requests.size}")
        }
        override suspend fun deleteSession(sessionId: String) {}
    }

    private class Recognizer : VoiceRecognizer {
        lateinit var events: VoiceEvents
        var released = false
        override fun start(events: VoiceEvents) { this.events = events }
        override fun stop() = Unit
        override fun release() { released = true }
    }

    @Test fun `new unsent conversation releases voice before clearing null session draft`() = runTest(dispatcher) {
        val saved = SavedStateHandle(); val vm = AppViewModel(Repository(), saved)
        val recognizer = Recognizer()
        val voice = VoiceController({ recognizer }, {}, vm::draft)
        vm.bindVoiceInput(voice::cancel)
        advanceUntilIdle()
        voice.start(true, ""); recognizer.events.partial("Discard this dictation")
        assertNull(vm.state.value.sessionId)
        assertEquals("Discard this dictation", vm.state.value.draft)
        vm.newConversation()
        assertTrue(recognizer.released)
        assertFalse(voice.state.active)
        assertNull(vm.state.value.sessionId)
        recognizer.events.partial("Late partial"); recognizer.events.final("Late final")
        assertEquals("", vm.state.value.draft)
        assertEquals("", saved.get<String>("draft"))
    }

    @Test fun `opening even the same saved session cancels voice and rejects discarded results`() = runTest(dispatcher) {
        val vm = AppViewModel(Repository(), SavedStateHandle())
        val session = Session("saved-session", "Saved", "")
        vm.open(session); advanceUntilIdle()
        val recognizer = Recognizer(); val voice = VoiceController({ recognizer }, {}, vm::draft)
        vm.bindVoiceInput(voice::cancel)
        voice.start(true, ""); recognizer.events.partial("Discard")
        vm.open(session)
        assertTrue(recognizer.released)
        recognizer.events.partial("Late partial"); recognizer.events.final("Late final")
        advanceUntilIdle()
        assertEquals(session.id, vm.state.value.sessionId)
        assertEquals("", vm.state.value.draft)
    }

    @Test fun `clearing the chat owner releases microphone and rejects identity stale callbacks`() = runTest(dispatcher) {
        val vm = AppViewModel(Repository(), SavedStateHandle()); advanceUntilIdle()
        val store = ViewModelStore().also { it.put("chat", vm) }
        val recognizer = Recognizer(); val voice = VoiceController({ recognizer }, {}, vm::draft)
        vm.bindVoiceInput(voice::cancel)
        voice.start(true, "")
        store.clear()
        assertTrue(recognizer.released)
        recognizer.events.final("Previous account")
        assertEquals("", vm.state.value.draft)
    }

    @Test fun `profile sign out cancels voice before asynchronous logout starts`() = runTest(dispatcher) {
        val vm = AppViewModel(Repository(), SavedStateHandle()); advanceUntilIdle()
        val recognizer = Recognizer(); val voice = VoiceController({ recognizer }, {}, vm::draft)
        vm.bindVoiceInput(voice::cancel)
        var logoutStarted = false
        val account = AccountControls(Account("owner", "owner@example.test", "Owner"), false, null) {
            assertTrue(recognizer.released)
            logoutStarted = true
            // A stalled or failed HTTP logout must not keep capturing audio.
        }.withVoiceCancellation(vm::cancelVoiceInput)
        voice.start(true, "")
        account.logout()
        assertTrue(logoutStarted)
        assertFalse(voice.state.active)
        recognizer.events.partial("Late partial"); recognizer.events.final("Late final")
        assertEquals("", vm.state.value.draft)
    }

    @Test fun `disposed voice binding cannot detach a newer screen recognizer`() = runTest(dispatcher) {
        val vm = AppViewModel(Repository(), SavedStateHandle()); advanceUntilIdle()
        val first = Recognizer(); val oldVoice = VoiceController({ first }, {}, vm::draft)
        val unbindOld = vm.bindVoiceInput(oldVoice::cancel)
        oldVoice.start(true, "")
        val second = Recognizer(); val newVoice = VoiceController({ second }, {}, vm::draft)
        vm.bindVoiceInput(newVoice::cancel)
        assertTrue(first.released)
        newVoice.start(true, "")
        unbindOld()
        assertFalse(second.released)
        vm.newConversation()
        assertTrue(second.released)
        second.events.final("Late final")
        assertEquals("", vm.state.value.draft)
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
