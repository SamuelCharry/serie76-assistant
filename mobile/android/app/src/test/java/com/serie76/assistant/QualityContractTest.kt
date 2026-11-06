package com.serie76.assistant

import com.serie76.assistant.data.*
import org.junit.Assert.*
import org.junit.Test

class QualityContractTest {
    @Test fun `new response preserves reply text and difference direction without decimal conversion`() {
        val response = wireJson.decodeFromString<ConversationResponse>("""{
          "session_id":"s", "message_id":"m", "answer":"Differences",
          "suggested_replies":["Compare A vs B","Show more","Cancel"],
          "comparison":{"models":["A","B"],"identical_fields_hidden":7,"rows":[
            {"field":"fla_60hz_a","label":"FLA 60 Hz","a":"1.20 A","b":"2.50 A","better":"a"},
            {"field":"enclosure","label":"Enclosure","a":"weatherproof","b":"explosionproof","better":null}
          ]}}""")
        assertEquals(listOf("Compare A vs B", "Show more", "Cancel"), response.suggestedReplies)
        assertEquals("1.20 A", response.comparison!!.rows.first().a)
        assertEquals(0, response.comparison!!.rows.first().better)
        assertNull(response.comparison!!.rows.last().better)
        assertEquals(7, response.comparison!!.identicalFieldsHidden)
    }

    @Test fun `old stored message has no chips or comparison by default`() {
        val message = wireJson.decodeFromString<Message>("""{"id":"old","role":"assistant","content":"Saved"}""")
        assertTrue(message.suggestedReplies.isEmpty())
        assertNull(message.comparison)
    }

    @Test fun `stored message retains exact chip messages and comparison models`() {
        val message = Message("id", "assistant", "Answer", suggestedReplies = listOf("Use 110 V", "On/Off service", "Cancel"),
            comparison = DifferenceComparison(listOf("A", "B"), emptyList(), 5))
        assertEquals("Use 110 V", message.suggestedReplies.first())
        assertEquals(2, message.comparison!!.models.size)
    }

    @Test
    fun `comparison now accepts more than two models`() {
        assertEquals(3, DifferenceComparison(listOf("A", "B", "C"), emptyList(), layout = "cards").models.size)
    }
}
