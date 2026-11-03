package com.serie76.assistant

import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

class ContractTest {
    @Test fun `JSON keeps exact decimal representation and unavailable states`() {
        val p = wireJson.decodeFromString<Product>("""{
          "base_part_number":"761A00-11300000/A",
          "measurements":{"fla_60hz_a":1.20,"motor_power_w":null},
          "field_status":{"fla_60hz_a":"reported","motor_power_w":"source_NA"},
          "future_field":"ignored"
        }""")
        assertEquals("1.20 A", measurement(p, TechnicalField("fla_60hz_a", "FLA", "A")))
        assertEquals("N/A", measurement(p, TechnicalField("motor_power_w", "Power", "W")))
        assertEquals("Not reported", measurement(p, TechnicalField("unknown", "Unknown", "W")))
        assertEquals("761A00-11300000/A", p.partNumber)
    }

    @Test fun `first request omits null session and continuation uses same identifier`() = runTest {
        MockWebServer().use { server ->
            server.start()
            repeat(2) { server.enqueue(MockResponse().setBody("""{"session_id":"session","message_id":"answer","answer":"Data","products":[]}""").setHeader("Content-Type", "application/json")) }
            val api = createRetrofit(server.url("/").toString()).create(ConversationApi::class.java)
            val repo = ApiConversationRepository(api)
            val first = repo.send("First", null)
            repo.send("Continue", first.sessionId)
            val body1 = Json.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            val body2 = Json.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertFalse(body1.containsKey("session_id"))
            assertEquals("session", body2["session_id"]!!.jsonPrimitive.content)
        }
    }
}
