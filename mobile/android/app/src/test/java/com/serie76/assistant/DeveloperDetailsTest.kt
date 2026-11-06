package com.serie76.assistant

import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.serialization.json.*
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

class DeveloperDetailsTest {
    @Test fun `seven taps inside three seconds toggle and reset`() {
        val taps = DeveloperUnlock()
        repeat(6) { assertFalse(taps.tap(it * 400L)) }
        assertTrue(taps.tap(2400))
        repeat(6) { assertFalse(taps.tap(2500L + it * 50)) }
        assertTrue(taps.tap(2800))
    }
    @Test fun `slow taps do not unlock and window slides`() {
        val taps = DeveloperUnlock()
        repeat(7) { assertFalse(taps.tap(it * 1000L)) }
        assertFalse(taps.tap(6100)); assertFalse(taps.tap(6200))
        assertFalse(taps.tap(6300)); assertTrue(taps.tap(6400))
    }
    @Test fun `exact three second boundary accepted but older taps excluded`() {
        val exact = DeveloperUnlock(); repeat(6) { assertFalse(exact.tap(it * 500L)) }
        assertTrue(exact.tap(3000))
        val late = DeveloperUnlock(); repeat(6) { assertFalse(late.tap(it * 500L)) }
        assertFalse(late.tap(3001))
    }
    @Test fun `debug icons require developer mode and assistant role`() {
        assertFalse(showDebugDetails(false, Message("a", "assistant", "answer")))
        assertFalse(showDebugDetails(true, Message("u", "user", "question")))
        assertTrue(showDebugDetails(true, Message("a", "assistant", "answer")))
    }
    @Test fun `sheet maps actual nested endpoint shape without losing false or zero`() {
        val response = wireJson.decodeFromString<DebugResponse>("""{"message_id":"a","session_id":"s","tool_calls":[{"name":"get_actuator","raw_parameters":{"part":"raw"},"parameters":{"part":"validated"},"merged_parameters":{"voltage":110},"validation":["ok"],"data":{"rows":[{"value":null}]}}],"debug":{"latency_ms":0,"attempts":0,"llm_called":false,"retrieval":{"examples":[{"similarity":0.8}],"concept_scores":{"torque":0.9}}}}""")
        val sections = debugSections(response)
        assertTrue(sections.any { it.title == "Tools called" && "get_actuator" in it.value.toString() })
        assertTrue(sections.any { it.title.contains("Raw parameters") && "raw" in it.value.toString() })
        assertTrue(sections.any { it.title.contains("Validated parameters") && "validated" in it.value.toString() })
        assertTrue(sections.any { it.title.contains("Returned data") && "null" in it.value.toString() })
        val metrics = sections.single { it.title == "Execution" }.value.jsonObject
        assertEquals(JsonPrimitive(false), metrics["llm_called"])
        assertEquals(JsonPrimitive(0), metrics["latency_ms"])
        assertTrue(sections.any { it.title == "Retrieval" && "concept_scores" in it.value.toString() })
    }
    @Test fun `legacy top level metrics remain supported and missing retrieval stays absent`() {
        val response = wireJson.decodeFromString<DebugResponse>("""{"message_id":"a","session_id":"s","tool_calls":[],"latency_ms":12,"llm_called":true}""")
        val sections = debugSections(response)
        assertEquals(JsonPrimitive(12), sections.single { it.title == "Execution" }.value.jsonObject["latency_ms"])
        assertFalse(sections.any { it.title == "Retrieval" })
    }
    @Test fun `resumed message id loads owner authenticated endpoint lazily`() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse().setBody("""{"message_id":"saved-answer","session_id":"s","tool_calls":[],"debug":{"attempts":0,"llm_called":false}}"""))
            val api = createRetrofit(server.url("/").toString(), bearer = { "synthetic-test-token" }).create(DebugApi::class.java)
            assertEquals(0, server.requestCount)
            val response = api.trace("saved-answer")
            val request = server.takeRequest()
            assertEquals("/api/messages/saved-answer/debug", request.path)
            assertEquals("Bearer synthetic-test-token", request.getHeader("Authorization"))
            assertEquals("saved-answer", response.messageId)
            assertEquals(JsonPrimitive(false), response.debug["llm_called"])
        }
    }
    @Test fun `missing raw parameters stay null and explicit validated parameters win`() {
        val response = wireJson.decodeFromString<DebugResponse>("""{"message_id":"a","session_id":"s","tool_calls":[{"name":null,"parameters":{"old":1},"validated_parameters":{"new":2},"data":{}}]}""")
        val sections = debugSections(response)
        assertEquals(JsonNull, sections.single { it.id == "0-raw" }.value)
        assertEquals("{\"new\":2}", sections.single { it.id == "0-validated" }.value.toString())
    }
}
