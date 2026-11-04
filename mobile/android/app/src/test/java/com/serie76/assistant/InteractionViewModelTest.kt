package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.test.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class InteractionViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun teardown() { Dispatchers.resetMain() }
    private val question = Interaction(questions = listOf(
        Question("service", "Which service?", listOf(QuestionOption("on_off", "On/Off"), QuestionOption("modulating", "Modulating"))),
        Question("voltage", "Which voltage?", listOf(QuestionOption("220", "220 V"))),
    ))
    private inner class Repository : ConversationRepository {
        val requests = mutableListOf<ConversationRequest>()
        var wait: CompletableDeferred<Unit>? = null
        var answer = ConversationResponse("s", "Full", "m", lead = "Lead", interaction = question,
            activeFilters = listOf(ActiveFilter("min_torque_nm", ">= 70 Nm")))
        var history = listOf(Message("old", "assistant", "Choose", interaction = question, activeFilters = answer.activeFilters))
        override suspend fun sessions(offset: Int) = SessionsPage(emptyList())
        override suspend fun messages(sessionId: String, before: Long?) = MessagesPage("s", "Saved", history)
        override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>, removeFilters: List<String>): ConversationResponse {
            requests += ConversationRequest(query, sessionId, answers, removeFilters)
            wait?.await()
            return answer
        }
    }
    private fun opened(repo: Repository): AppViewModel = AppViewModel(repo, SavedStateHandle()).also { it.open(Session("s", "Saved", "")) }

    @Test fun `history question advances edits and submits exactly once with new response metadata`() = runTest(dispatcher) {
        val repo = Repository(); val vm = opened(repo); advanceUntilIdle()
        vm.chooseAnswer("on_off"); vm.chooseAnswer("220")
        assertTrue(vm.state.value.question!!.reviewing); assertTrue(repo.requests.isEmpty())
        vm.editAnswer(0); vm.chooseAnswer("modulating")
        repo.wait = CompletableDeferred()
        vm.submitAnswers(); vm.submitAnswers(); runCurrent()
        assertNull(vm.state.value.question)
        assertEquals(1, repo.requests.size)
        assertEquals("Modulating · 220 V", repo.requests.single().query)
        assertEquals(mapOf("service" to "modulating", "voltage" to "220"), repo.requests.single().answers)
        repo.wait!!.complete(Unit); advanceUntilIdle()
        val message = vm.state.value.messages.last()
        assertEquals(question, message.interaction); assertEquals("Lead", message.lead)
        assertEquals(repo.answer.activeFilters, vm.state.value.activeFilters)
    }

    @Test fun `cancel clears card immediately and sends no structured answers`() = runTest(dispatcher) {
        val repo = Repository(); val vm = opened(repo); advanceUntilIdle()
        repo.answer = repo.answer.copy(interaction = null)
        vm.chooseAnswer("on_off"); vm.cancelQuestion()
        assertNull(vm.state.value.question)
        advanceUntilIdle()
        assertEquals(ConversationRequest("Cancel", "s"), repo.requests.single())
        assertNull(vm.state.value.question)
    }

    @Test fun `free text dismisses pending question on send and never attaches partial answers`() = runTest(dispatcher) {
        val repo = Repository(); val vm = opened(repo); advanceUntilIdle()
        vm.chooseAnswer("on_off"); vm.activateComposer()
        assertTrue(vm.state.value.composerActive)
        vm.draft("Actually show 110 V"); vm.send()
        assertNull(vm.state.value.question)
        advanceUntilIdle()
        assertEquals(ConversationRequest("Actually show 110 V", "s"), repo.requests.single())
    }

    @Test fun `typing dismisses suggestions even after clearing text and next answer resets dismissal`() = runTest(dispatcher) {
        val repo = Repository()
        repo.history = listOf(Message("old", "assistant", "Answer", suggestions = listOf("Next")))
        repo.answer = repo.answer.copy(interaction = null, suggestions = listOf("More"))
        val vm = opened(repo); advanceUntilIdle()
        assertFalse(vm.state.value.suggestionsDismissed)
        vm.draft("x"); vm.draft("")
        assertTrue(vm.state.value.suggestionsDismissed)
        vm.draft("Send"); vm.send(); advanceUntilIdle()
        assertFalse(vm.state.value.suggestionsDismissed)
        assertEquals(listOf("More"), vm.state.value.messages.last().suggestions)
    }

    @Test fun `removing current filter sends field and duplicate action is blocked`() = runTest(dispatcher) {
        val repo = Repository(); val vm = opened(repo); advanceUntilIdle()
        repo.answer = repo.answer.copy(activeFilters = emptyList(), interaction = null)
        vm.removeFilter(ActiveFilter("unknown", "Unknown")); runCurrent()
        assertTrue(repo.requests.isEmpty())
        val filter = vm.state.value.activeFilters.single()
        vm.removeFilter(filter); vm.removeFilter(filter); advanceUntilIdle()
        assertEquals(ConversationRequest("Remove >= 70 Nm", "s", removeFilters = listOf("min_torque_nm")), repo.requests.single())
        assertTrue(vm.state.value.activeFilters.isEmpty())
        vm.newConversation(); assertNull(vm.state.value.question)
    }
}
