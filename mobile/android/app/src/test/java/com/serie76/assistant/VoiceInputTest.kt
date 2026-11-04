package com.serie76.assistant

import com.serie76.assistant.ui.*
import org.junit.Assert.*
import org.junit.Test

class VoiceInputTest {
    private class Fake : VoiceRecognizer {
        lateinit var events: VoiceEvents
        var stopped = false
        var released = false
        override fun start(events: VoiceEvents) { this.events = events }
        override fun stop() { stopped = true }
        override fun release() { released = true }
    }
    @Test fun `partial and final replace only dictated suffix and never send`() {
        val fake = Fake(); var text = "Existing"
        val voice = VoiceController({ fake }, {}, { text = it })
        voice.start(true, text)
        fake.events.partial("motor")
        assertEquals("Existing motor", text)
        fake.events.partial("motor power")
        assertEquals("Existing motor power", text)
        fake.events.final("motor power?")
        assertEquals("Existing motor power?", text)
        assertEquals(VoicePhase.IDLE, voice.state.phase)
        assertTrue(fake.released)
    }
    @Test fun `stop waits for final and does not start another recognition`() {
        val fake = Fake(); val voice = VoiceController({ fake }, {}, {})
        voice.start(true, ""); voice.stop()
        assertTrue(fake.stopped)
        assertEquals(VoicePhase.FINISHING, voice.state.phase)
        fake.events.final("review me")
        assertEquals(VoicePhase.IDLE, voice.state.phase)
    }
    @Test fun `cancel rejects late callbacks and preserves typed draft`() {
        val fake = Fake(); var text = ""
        val voice = VoiceController({ fake }, {}, { text = it })
        voice.start(true, ""); fake.events.partial("partial"); voice.cancel()
        text = "typed"
        fake.events.final("late"); fake.events.error(VoiceError.NETWORK)
        assertEquals("typed", text)
        assertEquals(VoicePhase.IDLE, voice.state.phase)
        assertNull(voice.state.error)
        assertTrue(fake.released)
    }
    @Test fun `permission denied does not create recognizer`() {
        val voice = VoiceController({ error("must not create") }, {}, {})
        voice.start(false, "")
        assertEquals(VoiceError.PERMISSION, voice.state.error)
    }
    @Test fun `unavailable is explicit`() {
        val voice = VoiceController({ null }, {}, {})
        voice.start(true, "")
        assertEquals(VoiceError.UNAVAILABLE, voice.state.error)
    }
    @Test fun `errors release recognizer and preserve partial text`() {
        listOf(VoiceError.NO_MATCH, VoiceError.NETWORK, VoiceError.BUSY).forEach { error ->
            val fake = Fake(); var text = ""
            val voice = VoiceController({ fake }, {}, { text = it })
            voice.start(true, ""); fake.events.partial("review"); fake.events.error(error)
            assertEquals(error, voice.state.error); assertEquals("review", text); assertTrue(fake.released)
        }
    }
    @Test fun `old recognizer cannot overwrite a newer session`() {
        val first = Fake(); val second = Fake(); var next = first; var text = ""
        val voice = VoiceController({ next }, {}, { text = it })
        voice.start(true, ""); voice.cancel(); next = second; voice.start(true, "")
        first.events.final("stale"); second.events.final("new")
        assertEquals("new", text)
    }
    @Test fun `empty final keeps partial for review and reports no match`() {
        val fake = Fake(); var text = ""
        val voice = VoiceController({ fake }, {}, { text = it })
        voice.start(true, ""); fake.events.partial("review"); fake.events.final("")
        assertEquals("review", text); assertEquals(VoiceError.NO_MATCH, voice.state.error)
    }
    @Test fun `timeout releases a recognizer that never returns`() {
        val fake = Fake(); val voice = VoiceController({ fake }, {}, {})
        voice.start(true, ""); voice.stop(); voice.timeout()
        assertTrue(fake.released); assertFalse(voice.state.active)
        assertEquals(VoiceError.NO_MATCH, voice.state.error)
    }
    @Test fun `revoked permission is handled without crashing`() {
        val voice = VoiceController({ throw SecurityException("revoked") }, {}, {})
        voice.start(true, "")
        assertEquals(VoiceError.PERMISSION, voice.state.error)
    }
}
