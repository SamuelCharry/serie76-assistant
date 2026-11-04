package com.serie76.assistant

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModelStore
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import kotlinx.serialization.json.*
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException

@OptIn(ExperimentalCoroutinesApi::class)
class T8ContractTest {
    private val dispatcher = StandardTestDispatcher()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun teardown() { Dispatchers.resetMain() }

    @Test fun `new and legacy response shapes decode without losing action or recommendation`() {
        val json = """{"session_id":"s","message_id":"m","answer":"Results","interaction":{"kind":"question","questions":[{"id":"voltage","prompt":"Which voltage?","options":[{"value":"110","label":"110 V","count":21}]}]},"suggestions":["Legacy",{"label":"Compare top 2","action":{"type":"compare_top","args":{"n":2}}}],"recommendation":{"ranked_by":"Closest torque","total":10,"shown":3,"items":[{"part_number":"MODEL-A","reason":"Closest match","key_values":[{"label":"Torque","value":"80 Nm"}]}]},"comparison":{"layout":"cards","models":["A","B","C"],"rows":[],"key_fields":["torque"],"key_fields_reason":"Fields you filtered on"}}"""
        val response = wireJson.decodeFromString<ConversationResponse>(json)
        assertEquals(21, response.interaction!!.questions.single().options.single().count)
        assertEquals(Suggestion("Legacy"), response.suggestions!![0])
        assertEquals("compare_top", response.suggestions!![1].action!!.type)
        assertEquals("2", response.suggestions!![1].action!!.args["n"].toString())
        assertEquals("MODEL-A", response.recommendation!!.items.single().partNumber)
        assertEquals("Fields you filtered on", response.comparison!!.keyFieldsReason)
        val old = wireJson.decodeFromString<Message>("""{"id":"old","role":"assistant","content":"Earlier","suggestions":["Show more"]}""")
        assertEquals(Suggestion("Show more"), old.suggestions!!.single())
        assertNull(old.recommendation)
    }

    @Test fun `question stepper requires explicit navigation and review`() {
        val questions = listOf(Question("voltage", "Which voltage?", listOf(QuestionOption("110", "110 V", 21))),
            Question("enclosure", "Which enclosure?", listOf(QuestionOption("explosionproof", "Explosionproof", 10))))
        var state = QuestionStepper(questions)
        assertEquals(state, state.next())
        state = state.choose("110")
        assertEquals(0, state.index)
        state = state.next().choose("explosionproof").next()
        assertTrue(state.reviewing)
        assertEquals("110 V · Explosionproof", state.submission("s")!!.query)
        assertEquals(mapOf("voltage" to "110", "enclosure" to "explosionproof"), state.submission("s")!!.answers)
        state = state.back()
        assertEquals(1, state.index)
        assertTrue(state.next().reviewing)
    }

    @Test fun `suggestion action and plain string use distinct request payloads`() = runTest(dispatcher) {
        MockWebServer().use { server ->
            server.start()
            repeat(2) { server.enqueue(MockResponse().setBody("""{"session_id":"s","message_id":"m","answer":"OK"}""")) }
            val repo = ApiConversationRepository(createRetrofit(server.url("/").toString()).create(ConversationApi::class.java))
            val action = SuggestionAction("compare_top", kotlinx.serialization.json.buildJsonObject { put("n", 2) })
            val first = suggestionRequest(Suggestion("Compare top 2", action), "s")
            repo.send(first.query, first.sessionId, action = first.action)
            val second = suggestionRequest(Suggestion("Show more"), "s")
            repo.send(second.query, second.sessionId, action = second.action)
            val structured = wireJson.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertEquals("Compare top 2", structured["query"]!!.jsonPrimitive.content)
            assertEquals("compare_top", structured["action"]!!.jsonObject["type"]!!.jsonPrimitive.content)
            val legacy = wireJson.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertEquals("Show more", legacy["query"]!!.jsonPrimitive.content)
            assertFalse(legacy.containsKey("action"))
        }
    }

    @Test fun `delete waits five seconds and undo prevents HTTP DELETE`() = runTest(dispatcher) {
        val repo = FakeRepository()
        val vm = AppViewModel(repo, SavedStateHandle(), this)
        runCurrent()
        vm.open(repo.session); runCurrent()
        vm.requestDelete(repo.session); vm.confirmDelete()
        assertNull(vm.state.value.sessionId)
        assertTrue(vm.state.value.sessions.isEmpty())
        advanceTimeBy(4999); runCurrent()
        assertTrue(repo.deleted.isEmpty())
        vm.undoDelete(); advanceTimeBy(5000); runCurrent()
        assertTrue(repo.deleted.isEmpty())
        assertEquals(repo.session, vm.state.value.sessions.single())
        vm.requestDelete(repo.session); vm.confirmDelete()
        advanceTimeBy(5000); runCurrent()
        assertEquals(listOf("s"), repo.deleted)
    }

    @Test fun `delete API failure restores the conversation`() = runTest(dispatcher) {
        val repo = FakeRepository()
        repo.deleteFailure = true
        val vm = AppViewModel(repo, SavedStateHandle(), this)
        runCurrent()
        vm.requestDelete(repo.session); vm.confirmDelete()
        advanceTimeBy(5000); runCurrent()
        assertEquals(repo.session, vm.state.value.sessions.single())
        assertNotNull(vm.state.value.deleteNotice)
    }

    @Test fun `second deletion commits first immediately and undo restores only second`() = runTest(dispatcher) {
        val repo = FakeRepository()
        val second = Session("second", "Second", "2026-11-04T00:01:00Z")
        repo.allSessions += second
        val vm = AppViewModel(repo, SavedStateHandle(), this)
        runCurrent()
        vm.requestDelete(repo.session); vm.confirmDelete()
        vm.requestDelete(second); vm.confirmDelete()
        runCurrent()
        assertEquals(listOf("s"), repo.deleted)
        assertEquals("second", vm.state.value.pendingDelete?.id)
        vm.undoDelete()
        advanceTimeBy(5000); runCurrent()
        assertEquals(listOf("s"), repo.deleted)
        assertEquals(listOf("second"), vm.state.value.sessions.map { it.id })
        vm.refreshSessions(); runCurrent()
        assertEquals(listOf("second"), vm.state.value.sessions.map { it.id })
    }

    @Test fun `clearing ViewModel commits a pending deletion`() = runTest(dispatcher) {
        val repo = FakeRepository()
        val vm = AppViewModel(repo, SavedStateHandle(), this)
        val store = ViewModelStore()
        store.put("chat", vm)
        runCurrent()
        vm.requestDelete(repo.session); vm.confirmDelete()
        store.clear()
        runCurrent()
        assertEquals(listOf("s"), repo.deleted)
        advanceTimeBy(5000); runCurrent()
        assertEquals(listOf("s"), repo.deleted)
    }

    @Test fun `failed earlier deletion restores its row while second undo remains available`() = runTest(dispatcher) {
        val repo = FakeRepository()
        val second = Session("second", "Second", "2026-11-04T00:01:00Z")
        repo.allSessions += second
        repo.deleteFailure = true
        val vm = AppViewModel(repo, SavedStateHandle(), this)
        runCurrent()
        vm.requestDelete(repo.session); vm.confirmDelete()
        vm.requestDelete(second); vm.confirmDelete()
        runCurrent()
        assertEquals(listOf("s"), vm.state.value.sessions.map { it.id })
        assertEquals("second", vm.state.value.pendingDelete?.id)
        vm.undoDelete()
        assertEquals(setOf("s", "second"), vm.state.value.sessions.map { it.id }.toSet())
        assertTrue(repo.deleted.isEmpty())
    }

    @Test fun `empty combination returns to review with inline detail`() = runTest(dispatcher) {
        val repo = FakeRepository()
        repo.failure = HttpException(retrofit2.Response.error<Unit>(422,
            """{"error_code":"empty_combination","detail":"110 V conflicts with Explosionproof."}"""
                .toResponseBody("application/json".toMediaType())))
        val vm = AppViewModel(repo, SavedStateHandle())
        runCurrent(); vm.open(repo.session); runCurrent()
        vm.chooseAnswer("110"); vm.nextQuestion(); vm.submitAnswers(); runCurrent()
        assertTrue(vm.state.value.question!!.reviewing)
        assertEquals("110 V conflicts with Explosionproof.", vm.state.value.questionError)
        assertNull(vm.state.value.sendError)
        assertFalse(vm.state.value.needsReconcile)
    }

    private class FakeRepository : ConversationRepository {
        val session = Session("s", "Saved", "2026-11-04T00:00:00Z")
        val allSessions = mutableListOf(session)
        val deleted = mutableListOf<String>()
        var failure: Exception? = null
        var deleteFailure = false
        override suspend fun sessions(offset: Int) = SessionsPage(allSessions.filterNot { it.id in deleted })
        override suspend fun messages(sessionId: String, before: Long?) = MessagesPage("s", "Saved", listOf(
            Message("m", "assistant", "Choose", interaction = Interaction(questions = listOf(
                Question("voltage", "Which voltage?", listOf(QuestionOption("110", "110 V", 21))))))))
        override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>,
                                  removeFilters: List<String>, action: SuggestionAction?): ConversationResponse {
            failure?.let { throw it }
            return ConversationResponse("s", "OK", "reply")
        }
        override suspend fun deleteSession(sessionId: String) {
            if (deleteFailure) throw java.io.IOException("offline")
            deleted += sessionId
        }
    }
}
