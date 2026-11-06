package com.serie76.assistant.ui

enum class VoicePhase { IDLE, LISTENING, FINISHING }
enum class VoiceError(val message: String) {
    PERMISSION("Microphone permission is needed for voice input"),
    UNAVAILABLE("Voice input isn't available on this device"),
    NO_MATCH("Didn't catch that — try again"),
    NETWORK("Voice input couldn't connect — try again"),
    BUSY("Voice input is busy — try again"),
    OTHER("Voice input stopped — try again"),
}
data class VoiceState(val phase: VoicePhase = VoicePhase.IDLE, val error: VoiceError? = null) {
    val active: Boolean get() = phase != VoicePhase.IDLE
}
interface VoiceEvents {
    fun partial(text: String)
    fun final(text: String)
    fun error(error: VoiceError)
}
interface VoiceRecognizer {
    fun start(events: VoiceEvents)
    fun stop()
    /** Cancel and destroy the platform resource. */
    fun release()
}

/** Main-thread controller. Generation guards reject callbacks after typing/navigation/disposal. */
class VoiceController(private val create: () -> VoiceRecognizer?, private val changed: (VoiceState) -> Unit,
                      private val draft: (String) -> Unit) {
    var state = VoiceState(); private set
    private var recognizer: VoiceRecognizer? = null
    private var generation = 0
    private fun update(value: VoiceState) { state = value; changed(value) }
    fun start(permission: Boolean, existing: String) {
        if (state.active) return
        if (!permission) { update(VoiceState(error = VoiceError.PERMISSION)); return }
        val token = ++generation
        val prefix = existing.trimEnd().let { if (it.isEmpty()) "" else "$it " }
        try {
            val engine = create() ?: run { update(VoiceState(error = VoiceError.UNAVAILABLE)); return }
            recognizer = engine
            update(VoiceState(VoicePhase.LISTENING))
            engine.start(object : VoiceEvents {
                override fun partial(text: String) { if (token == generation && text.isNotBlank()) draft((prefix + text).take(4000)) }
                override fun final(text: String) {
                    if (token != generation) return
                    partial(text)
                    finish(if (text.isBlank()) VoiceError.NO_MATCH else null)
                }
                override fun error(error: VoiceError) { if (token == generation) finish(error) }
            })
        } catch (_: SecurityException) { finish(VoiceError.PERMISSION) }
        catch (_: Exception) { finish(VoiceError.UNAVAILABLE) }
    }
    fun stop() {
        if (state.phase != VoicePhase.LISTENING) return
        update(VoiceState(VoicePhase.FINISHING))
        try { recognizer?.stop() } catch (_: Exception) { finish(VoiceError.OTHER) }
    }
    fun cancel() { finish(null) }
    fun timeout() { if (state.active) finish(VoiceError.NO_MATCH) }
    private fun finish(error: VoiceError?) {
        generation++
        val engine = recognizer; recognizer = null
        runCatching { engine?.release() }
        update(VoiceState(error = error))
    }
}
