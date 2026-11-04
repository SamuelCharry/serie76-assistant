package com.serie76.assistant.ui

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.serie76.assistant.data.*
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

data class AppState(
    val screen: String = "chat",
    val sessions: List<Session> = emptyList(),
    val sessionsLoading: Boolean = false,
    val sessionsError: String? = null,
    val sessionsHaveMore: Boolean = false,
    val sessionId: String? = null,
    val title: String = "New conversation",
    val messages: List<Message> = emptyList(),
    val historyLoading: Boolean = false,
    val historyError: String? = null,
    val historyBefore: Long? = null,
    val draft: String = "",
    val sending: Boolean = false,
    val sendError: String? = null,
    val needsReconcile: Boolean = false,
    val question: QuestionStepper? = null,
    val composerActive: Boolean = false,
    val suggestionsDismissed: Boolean = false,
    val questionError: String? = null,
    val deleteCandidate: Session? = null,
    val pendingDelete: Session? = null,
    val committingDeleteIds: Set<String> = emptySet(),
    val deleteNotice: String? = null,
) {
    val activeFilters: List<ActiveFilter> get() = messages.lastOrNull { it.role == "assistant" }?.activeFilters.orEmpty()
    val canSend: Boolean get() = !sending && !historyLoading && historyError == null && !needsReconcile
}

private fun pendingQuestion(message: Message?): QuestionStepper? = message?.takeIf { it.role == "assistant" }
    ?.interaction?.takeIf { it.kind == "question" && it.questions.isNotEmpty() }?.let { QuestionStepper(it.questions) }

class AppViewModel(private val repository: ConversationRepository, private val saved: SavedStateHandle,
                   private val deleteCommitScope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)) : ViewModel() {
    private val mutable = MutableStateFlow(AppState(
        screen = saved.get<String>("screen")?.takeIf { it == "sessions" } ?: "chat", sessionId = saved["sessionId"], draft = saved["draft"] ?: "",
        // A process may have died after the server committed a request. Reconcile before resend.
        needsReconcile = saved["inFlight"] ?: false,
    ))
    val state = mutable.asStateFlow()
    private var historyJob: Job? = null
    private var sessionsJob: Job? = null
    private var threadGeneration = 0
    private var deleteJob: Job? = null

    init {
        refreshSessions()
        state.value.sessionId?.let { loadHistory(it) }
    }

    fun refreshSessions(more: Boolean = false) {
        if (more && state.value.sessionsLoading) return
        sessionsJob?.cancel()
        sessionsJob = viewModelScope.launch {
            mutable.update { it.copy(sessionsLoading = true, sessionsError = null) }
            try {
                val offset = if (more) state.value.sessions.size else 0
                val page = repository.sessions(offset)
                mutable.update { it.copy(sessions = (if (more) it.sessions + page.sessions else page.sessions).distinctBy(Session::id)
                    .filterNot { session -> session.id == it.pendingDelete?.id || session.id in it.committingDeleteIds },
                    sessionsHaveMore = page.sessions.size == page.limit, sessionsLoading = false) }
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) { mutable.update { it.copy(sessionsLoading = false, sessionsError = failureMessage(error)) } }
        }
    }

    fun newConversation() {
        if (state.value.sending) return
        historyJob?.cancel()
        threadGeneration++
        saved["sessionId"] = null
        saved["draft"] = ""
        saved["screen"] = "chat"
        saved["inFlight"] = false
        mutable.update { AppState(screen = "chat", sessions = it.sessions, sessionsHaveMore = it.sessionsHaveMore,
            pendingDelete = it.pendingDelete, committingDeleteIds = it.committingDeleteIds,
            deleteNotice = it.deleteNotice) }
    }

    fun open(session: Session) {
        if (state.value.sending) return
        threadGeneration++
        saved["sessionId"] = session.id
        saved["screen"] = "chat"
        saved["draft"] = ""
        mutable.update { it.copy(screen = "chat", sessionId = session.id, title = session.title,
            messages = emptyList(), draft = "", sendError = null, needsReconcile = false, historyBefore = null,
            question = null, composerActive = false, suggestionsDismissed = false) }
        loadHistory(session.id)
    }

    fun back() {
        showConversations()
    }

    fun showConversations() {
        saved["screen"] = "sessions"
        mutable.update { it.copy(screen = "sessions") }
        refreshSessions()
    }

    fun dismissConversations() {
        saved["screen"] = "chat"
        mutable.update { it.copy(screen = "chat") }
    }

    fun draft(value: String) {
        if (value.length > 4000) return
        saved["draft"] = value
        mutable.update { it.copy(draft = value, suggestionsDismissed = it.suggestionsDismissed || value.isNotEmpty(),
            composerActive = it.composerActive || value.isNotEmpty()) }
    }

    fun activateComposer() { mutable.update { it.copy(composerActive = true) } }
    fun chooseAnswer(value: String) {
        if (state.value.canSend) mutable.update { it.copy(question = it.question?.choose(value), questionError = null) }
    }
    fun nextQuestion() { if (state.value.canSend) mutable.update { it.copy(question = it.question?.next(), questionError = null) } }
    fun previousQuestion() { if (state.value.canSend) mutable.update { it.copy(question = it.question?.back(), questionError = null) } }
    fun editAnswer(index: Int) {
        if (state.value.canSend) mutable.update { it.copy(question = it.question?.edit(index), questionError = null) }
    }
    fun submitAnswers() { state.value.question?.submission(state.value.sessionId)?.let(::sendRequest) }
    fun cancelQuestion() {
        if (state.value.question != null) sendRequest(cancelQuestionRequest(state.value.sessionId))
    }
    fun removeFilter(filter: ActiveFilter) {
        if (filter in state.value.activeFilters) sendRequest(removeFilterRequest(filter, state.value.sessionId))
    }
    fun sendSuggestion(suggestion: Suggestion) { sendRequest(suggestionRequest(suggestion, state.value.sessionId)) }
    fun requestDelete(session: Session) { mutable.update { it.copy(deleteCandidate = session) } }
    fun cancelDelete() { mutable.update { it.copy(deleteCandidate = null) } }
    fun confirmDelete() {
        val session = state.value.deleteCandidate ?: return
        commitPendingDelete()
        mutable.update { it.copy(sessions = it.sessions.filterNot { item -> item.id == session.id },
            deleteCandidate = null, pendingDelete = session, deleteNotice = "Conversation deleted") }
        if (state.value.sessionId == session.id) newConversation()
        deleteJob = viewModelScope.launch {
            delay(5000)
            commitPendingDelete()
        }
    }
    private fun commitPendingDelete() {
        val session = state.value.pendingDelete ?: return
        deleteJob?.cancel()
        deleteJob = null
        mutable.update { it.copy(pendingDelete = null, committingDeleteIds = it.committingDeleteIds + session.id,
            deleteNotice = null) }
        // This scope outlives ViewModel.clear(), so a confirmed deletion is not lost with the screen.
        deleteCommitScope.launch {
            try {
                repository.deleteSession(session.id)
                mutable.update { it.copy(committingDeleteIds = it.committingDeleteIds - session.id) }
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) { mutable.update { it.copy(
                sessions = (it.sessions + session).distinctBy(Session::id),
                committingDeleteIds = it.committingDeleteIds - session.id,
                deleteNotice = failureMessage(error), sessionsError = failureMessage(error)) } }
        }
    }
    fun undoDelete() {
        deleteJob?.cancel()
        mutable.update { it.copy(sessions = (it.sessions + listOfNotNull(it.pendingDelete)).distinctBy(Session::id),
            pendingDelete = null, deleteNotice = null) }
    }
    fun clearDeleteNotice() { mutable.update { it.copy(deleteNotice = null) } }

    override fun onCleared() {
        commitPendingDelete()
        super.onCleared()
    }

    fun loadHistory(sessionId: String? = state.value.sessionId, older: Boolean = false) {
        val targetId = sessionId ?: return
        historyJob?.cancel()
        val generation = threadGeneration
        historyJob = viewModelScope.launch {
            mutable.update { it.copy(historyLoading = true, historyError = null) }
            try {
                val before = if (older) state.value.historyBefore else null
                val page = repository.messages(targetId, before)
                if (generation != threadGeneration) return@launch
                saved["inFlight"] = false
                mutable.update { it.copy(title = page.title, historyLoading = false,
                    messages = (if (older) page.messages + it.messages else page.messages).distinctBy(Message::id),
                    historyBefore = page.nextBefore, needsReconcile = false,
                    question = if (older) it.question else pendingQuestion(page.messages.lastOrNull()),
                    composerActive = if (older) it.composerActive else it.draft.isNotEmpty(),
                    suggestionsDismissed = if (older) it.suggestionsDismissed else false) }
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) { mutable.update { it.copy(historyLoading = false, historyError = failureMessage(error)) } }
        }
    }

    fun send() {
        sendRequest(ConversationRequest(state.value.draft.trim(), state.value.sessionId))
    }

    private fun sendRequest(request: ConversationRequest) {
        val current = state.value
        val query = request.query
        if (query.isBlank() || !current.canSend) return
        val generation = threadGeneration
        saved["inFlight"] = true
        saved["draft"] = query
        mutable.update { it.copy(sending = true, sendError = null, draft = query,
            question = null, questionError = null, suggestionsDismissed = true, composerActive = false) }
        viewModelScope.launch {
            try {
                val response = repository.send(query, current.sessionId, request.answers, request.removeFilters, request.action)
                if (generation == threadGeneration) {
                    saved["sessionId"] = response.sessionId
                    saved["draft"] = ""
                    saved["inFlight"] = false
                    val message = Message(response.messageId, "assistant", response.answer, response.products,
                        suggestedReplies = response.suggestedReplies, comparison = response.comparison, lead = response.lead,
                        interaction = response.interaction, suggestions = response.suggestions,
                        recommendation = response.recommendation, activeFilters = response.activeFilters)
                    mutable.update { it.copy(sessionId = response.sessionId, title = if (current.sessionId == null) query.take(100) else it.title,
                        draft = "", sending = false, question = pendingQuestion(message), suggestionsDismissed = false,
                        messages = it.messages + listOf(Message(UUID.randomUUID().toString(), "user", query), message)) }
                }
                refreshSessions()
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) {
                val combination = if (request.answers.isNotEmpty()) emptyCombinationMessage(error) else null
                if (combination != null) {
                    saved["inFlight"] = false
                    saved["draft"] = ""
                    mutable.update { it.copy(sending = false, draft = "", question = current.question,
                        questionError = combination, needsReconcile = false) }
                } else mutable.update { it.copy(sending = false, sendError = failureMessage(error), needsReconcile = true) }
            }
        }
    }

    fun reconcile() {
        val id = state.value.sessionId
        if (id != null) loadHistory(id) else back()
    }

}
