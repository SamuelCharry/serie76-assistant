package com.serie76.assistant

import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import org.junit.Assert.*
import org.junit.Test

class ConversationPresentationTest {
    private val questions = listOf(
        Question("service", "Which service?", listOf(QuestionOption("on_off", "On/Off"), QuestionOption("modulating", "Modulating"))),
        Question("voltage", "Which voltage?", listOf(QuestionOption("220", "220 V"))),
        Question("phase", "How many phases?", listOf(QuestionOption("1", "1 phase"))),
    )

    @Test fun `stepper advances to review and edits a reviewed answer before submit`() {
        var stepper = QuestionStepper(questions)
        assertEquals(0, stepper.index); assertFalse(stepper.reviewing)
        assertNull(stepper.submission("s"))
        stepper = stepper.choose("on_off")
        assertEquals(1, stepper.index)
        stepper = stepper.choose("220").choose("1")
        assertTrue(stepper.reviewing)
        assertEquals(listOf("Which service? → On/Off", "Which voltage? → 220 V", "How many phases? → 1 phase"), stepper.reviewLines)
        val request = stepper.submission("s")!!
        assertEquals("On/Off · 220 V · 1 phase", request.query)
        assertEquals(mapOf("service" to "on_off", "voltage" to "220", "phase" to "1"), request.answers)
        assertEquals("s", request.sessionId)
        stepper = stepper.edit(0).choose("modulating")
        assertTrue(stepper.reviewing)
        assertEquals("Modulating · 220 V · 1 phase", stepper.submission("s")!!.query)
    }

    @Test fun `invalid option cannot advance or corrupt answers`() {
        val stepper = QuestionStepper(questions)
        assertEquals(stepper, stepper.choose("invented"))
        assertEquals(stepper, stepper.edit(4))
    }

    @Test fun `cancel sends readable query without answers`() {
        val request = cancelQuestionRequest("s")
        assertEquals("Cancel", request.query); assertTrue(request.answers.isEmpty())
        assertTrue(request.removeFilters.isEmpty()); assertEquals("s", request.sessionId)
    }

    @Test fun `suggestions are optional capped and suppressed while typing or asking`() {
        val message = Message("m", "assistant", "Answer", suggestions = listOf("One", "Two", "Three", "Four"))
        assertEquals(listOf("One", "Two", "Three"), visibleSuggestions(message, "", false))
        assertTrue(visibleSuggestions(message, "typing", false).isEmpty())
        assertTrue(visibleSuggestions(message, "", true).isEmpty())
        assertTrue(visibleSuggestions(message.copy(interaction = Interaction(questions = questions)), "", false).isEmpty())
        assertEquals(listOf("Old"), visibleSuggestions(message.copy(suggestions = null, suggestedReplies = listOf("Old")), "", false))
        assertTrue(visibleSuggestions(message.copy(suggestions = emptyList(), suggestedReplies = listOf("Old")), "", false).isEmpty())
    }

    @Test fun `filter removal contains only the requested field and readable label`() {
        val request = removeFilterRequest(ActiveFilter("min_torque_nm", ">= 70 Nm"), "s")
        assertEquals("Remove >= 70 Nm", request.query)
        assertEquals(listOf("min_torque_nm"), request.removeFilters)
        assertTrue(request.answers.isEmpty())
    }

    @Test fun `comparison hidden toggle preserves original rows and better index`() {
        val comparison = DifferenceComparison(listOf("A", "B"), listOf(DifferenceRow("torque", "Torque", values = listOf("80 Nm", "100 Nm"), better = 1)),
            hiddenRows = listOf(DifferenceRow("voltage", "Supply", values = listOf("220 V", "220 V"))))
        assertEquals(1, comparison.visibleRows(false).size)
        assertEquals(2, comparison.visibleRows(true).size)
        assertEquals(1, comparison.visibleRows(true).first().better)
        assertNull(comparison.visibleRows(true).last().better)
        assertEquals(1, comparison.visibleRows(false).size)
        assertEquals("761A00\n-11300000/A", comparisonModelTitle("761A00-11300000/A"))
    }

    @Test fun `three model cards select four fields in server order for every model`() {
        val fields = (1..5).map { n -> DifferenceRow("f$n", "Field $n", values = listOf("A$n", "B$n", "C$n")) }
        val comparison = DifferenceComparison(listOf("A", "B", "C"), fields, layout = "cards", keyFields = listOf("f4", "f2", "f1", "f3"))
        for (index in 0..2) {
            val values = comparison.cardFields(index)
            assertEquals(4, values.size)
            assertEquals(listOf("Field 4", "Field 2", "Field 1", "Field 3"), values.map { it.first })
            assertEquals("${comparison.models[index]}4", values.first().second)
        }
    }

    @Test fun `greeting uses first server name and falls back for missing or blank name`() {
        assertEquals("Hello, Samuel", greeting("  Samuel Charry  "))
        assertEquals("Hello, Ana", greeting("Ana\tMaria"))
        assertEquals("Hello", greeting(null)); assertEquals("Hello", greeting("  "))
    }

    @Test fun `lead replaces answer only when a product or comparison is shown`() {
        val message = Message("m", "assistant", "Full answer", lead = "Short lead")
        assertEquals("Full answer", message.displayText())
        assertEquals("Short lead", message.copy(products = listOf(Product("A"))).displayText())
        assertEquals("Short lead", message.copy(comparison = DifferenceComparison(listOf("A", "B"), emptyList())).displayText())
        assertEquals("Full answer", message.copy(lead = null, products = listOf(Product("A"))).displayText())
    }
}
