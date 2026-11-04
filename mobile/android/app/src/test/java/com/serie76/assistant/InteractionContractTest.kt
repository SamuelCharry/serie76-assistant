package com.serie76.assistant

import com.serie76.assistant.data.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.SocketPolicy
import org.junit.Assert.*
import org.junit.Test

class InteractionContractTest {
    @Test fun `question response and persisted message preserve all additive fields`() = runTest {
        MockWebServer().use { server ->
            server.start()
            val fields = """"lead":"Choose a supply.","interaction":{"kind":"question","questions":[{"id":"service","prompt":"Which service?","options":[{"value":"on_off","label":"On/Off"}]}]},"suggestions":[],"active_filters":[{"field":"supply_voltage_v","label":"110 V"}]"""
            server.enqueue(MockResponse().setBody("""{"session_id":"s","message_id":"m","answer":"Full answer",$fields}"""))
            server.enqueue(MockResponse().setBody("""{"session_id":"s","title":"Saved","messages":[{"id":"m","role":"assistant","content":"Full answer",$fields}]}"""))
            val repo = ApiConversationRepository(createRetrofit(server.url("/").toString()).create(ConversationApi::class.java))
            val response = repo.send("Find", null)
            val message = repo.messages("s").messages.single()
            assertEquals("Choose a supply.", response.lead)
            assertEquals(response.interaction, message.interaction)
            assertEquals("on_off", message.interaction!!.questions.single().options.single().value)
            assertEquals("Which service?", message.interaction!!.questions.single().prompt)
            assertEquals(response.activeFilters, message.activeFilters)
            assertEquals("110 V", message.activeFilters.single().label)
            assertEquals(emptyList<String>(), message.suggestions)
        }
    }

    @Test fun `legacy messages and responses default safely`() {
        val message = wireJson.decodeFromString<Message>("""{"id":"m","role":"assistant","content":"Old"}""")
        val response = wireJson.decodeFromString<ConversationResponse>("""{"session_id":"s","message_id":"m","answer":"Old"}""")
        assertNull(message.interaction); assertNull(message.lead); assertNull(message.suggestions)
        assertTrue(message.activeFilters.isEmpty()); assertNull(message.comparison)
        assertNull(response.interaction); assertNull(response.lead); assertNull(response.suggestions)
        assertTrue(response.activeFilters.isEmpty())
    }

    @Test fun `table and cards preserve exact numeric text and directions`() {
        val table = wireJson.decodeFromString<DifferenceComparison>("""{"layout":"table","models":["A","B"],"summary":"B wins.","assumptions":"More torque is better.","rows":[{"field":"torque","label":"Torque","values":["80.00 Nm","100 Nm"],"better":1}],"hidden_rows":[{"field":"voltage","label":"Supply","values":["220 V","220 V"]}],"key_fields":[]}""")
        assertEquals("table", table.layout); assertEquals("B wins.", table.summary)
        assertEquals("More torque is better.", table.assumptions)
        assertEquals(1, table.rows.single().better); assertEquals("80.00 Nm", table.rows.single().displayValues.first())
        assertNull(table.hiddenRows.single().better)
        val cards = wireJson.decodeFromString<DifferenceComparison>("""{"layout":"cards","models":["A","B","C"],"summary":"Three models","assumptions":"","rows":[{"field":"torque","label":"Torque","values":["80 Nm","100 Nm","N/A"],"better":null}],"hidden_rows":[],"key_fields":["torque"]}""")
        assertEquals(3, cards.models.size); assertEquals(listOf("torque"), cards.keyFields)
        assertEquals("N/A", cards.rows.single().displayValues.last())
    }

    @Test fun `structured request sends exact answers and filter removal without aliases`() = runTest {
        MockWebServer().use { server ->
            server.start()
            repeat(2) { server.enqueue(MockResponse().setBody("""{"session_id":"s","message_id":"m","answer":"OK"}""")) }
            val repo = ApiConversationRepository(createRetrofit(server.url("/").toString()).create(ConversationApi::class.java))
            repo.send("On/Off · 220 V", "s", mapOf("service" to "on_off", "supply_voltage_v" to "220"))
            repo.send("Remove 110 V", "s", removeFilters = listOf("supply_voltage_v"))
            val answers = wireJson.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertEquals("on_off", answers["answers"]!!.jsonObject["service"]!!.jsonPrimitive.content)
            assertEquals("On/Off · 220 V", answers["query"]!!.jsonPrimitive.content)
            assertFalse(answers.containsKey("remove_filters"))
            val removal = wireJson.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertEquals("supply_voltage_v", removal["remove_filters"]!!.jsonArray.single().jsonPrimitive.content)
            assertFalse(removal.containsKey("answers"))
        }
    }

    @Test fun `server closed connection is not reused on the next POST`() = runTest {
        MockWebServer().use { server ->
            server.start()
            val response = """{"session_id":"s","message_id":"m","answer":"OK"}"""
            server.enqueue(MockResponse().setBody(response).setHeader("Connection", "close").setSocketPolicy(SocketPolicy.DISCONNECT_AT_END))
            server.enqueue(MockResponse().setBody(response))
            val retrofit = createRetrofit(server.url("/").toString())
            val client = retrofit.callFactory() as okhttp3.OkHttpClient
            assertFalse(client.retryOnConnectionFailure)
            val repo = ApiConversationRepository(retrofit.create(ConversationApi::class.java))
            repo.send("First", null)
            assertEquals("OK", repo.send("Next", "s").answer)
            assertEquals(0, server.takeRequest().sequenceNumber)
            assertEquals(0, server.takeRequest().sequenceNumber)
            assertEquals(2, server.requestCount)
        }
    }
}
