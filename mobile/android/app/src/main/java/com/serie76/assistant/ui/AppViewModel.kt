package com.serie76.assistant.ui

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.serie76.assistant.data.*
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

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
    val debugMessageId: String? = null,
)

class AppViewModel(private val repository: ConversationRepository, private val saved: SavedStateHandle) : ViewModel() {
    private val mutable = MutableStateFlow(AppState(
        screen = saved["screen"] ?: "chat", sessionId = saved["sessionId"], draft = saved["draft"] ?: "",
        // A process may have died after the server committed a request. Reconcile before resend.
        needsReconcile = saved["inFlight"] ?: false,
        debugMessageId = saved["debugMessageId"],
    ))
    val state = mutable.asStateFlow()
    private var historyJob: Job? = null
    private var sessionsJob: Job? = null
    private var threadGeneration = 0

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
                mutable.update { it.copy(sessions = (if (more) it.sessions + page.sessions else page.sessions).distinctBy(Session::id),
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
        mutable.update { AppState(screen = "chat", sessions = it.sessions, sessionsHaveMore = it.sessionsHaveMore) }
    }

    fun open(session: Session) {
        if (state.value.sending) return
        threadGeneration++
        saved["sessionId"] = session.id
        saved["screen"] = "chat"
        saved["draft"] = ""
        mutable.update { it.copy(screen = "chat", sessionId = session.id, title = session.title,
            messages = emptyList(), draft = "", sendError = null, needsReconcile = false, historyBefore = null) }
        loadHistory(session.id)
    }

    fun back() {
        if (state.value.screen == "debug") {
            saved["screen"] = "chat"
            mutable.update { it.copy(screen = "chat") }
        } else {
            saved["screen"] = "sessions"
            mutable.update { it.copy(screen = "sessions") }
            refreshSessions()
        }
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
        mutable.update { it.copy(draft = value) }
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
                    historyBefore = page.nextBefore, needsReconcile = false) }
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) { mutable.update { it.copy(historyLoading = false, historyError = failureMessage(error)) } }
        }
    }

    fun send() {
        val current = state.value
        val query = current.draft.trim()
        if (query.isEmpty() || current.sending || current.historyLoading || current.historyError != null || current.needsReconcile) return
        val generation = threadGeneration
        saved["inFlight"] = true
        mutable.update { it.copy(sending = true, sendError = null) }
        viewModelScope.launch {
            try {
                val response = repository.send(query, current.sessionId)
                if (generation == threadGeneration) {
                    saved["sessionId"] = response.sessionId
                    saved["draft"] = ""
                    saved["inFlight"] = false
                    mutable.update { it.copy(sessionId = response.sessionId, title = if (current.sessionId == null) query.take(100) else it.title,
                        draft = "", sending = false,
                        messages = it.messages + listOf(Message(UUID.randomUUID().toString(), "user", query),
                            Message(response.messageId, "assistant", response.answer, response.products))) }
                }
                refreshSessions()
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) {
                mutable.update { it.copy(sending = false, sendError = failureMessage(error), needsReconcile = true) }
            }
        }
    }

    fun reconcile() {
        val id = state.value.sessionId
        if (id != null) loadHistory(id) else back()
    }

    fun debug() {
        saved["screen"] = "debug"
        mutable.update { it.copy(screen = "debug") }
    }

    fun debugMessage(id: String) {
        saved["debugMessageId"] = id
        mutable.update { it.copy(debugMessageId = id) }
    }
}
