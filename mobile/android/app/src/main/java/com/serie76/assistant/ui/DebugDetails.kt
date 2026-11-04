package com.serie76.assistant.ui

import com.serie76.assistant.data.DebugResponse
import com.serie76.assistant.data.Message
import kotlinx.serialization.json.*

/** Uses monotonic elapsed milliseconds; a completed gesture clears its window. */
class DeveloperUnlock {
    private val taps = ArrayDeque<Long>()
    fun tap(now: Long): Boolean {
        if (taps.lastOrNull()?.let { now < it } == true) taps.clear()
        while (taps.firstOrNull()?.let { now - it > 3000 } == true) taps.removeFirst()
        taps.addLast(now)
        if (taps.size < 7) return false
        taps.clear()
        return true
    }
}

fun showDebugDetails(enabled: Boolean, message: Message) = enabled && message.role == "assistant"
const val DEBUG_DISABLED = "Backend debug is disabled (DEV_DEBUG=false)"
data class DebugSection(val id: String, val title: String, val value: JsonElement)

/** Retains backend values exactly; never substitutes catalogue or visible card data. */
fun debugSections(response: DebugResponse): List<DebugSection> = buildList {
    add(DebugSection("tools", "Tools called", JsonArray(response.toolCalls.map { it.name?.let(::JsonPrimitive) ?: JsonNull })))
    response.toolCalls.forEachIndexed { index, call ->
        val title = "${index + 1}. ${call.name ?: "Unnamed tool"}"
        fun section(key: String, label: String, value: JsonElement?) {
            if (value != null && value != JsonNull) add(DebugSection("$index-$key", "$title · $label", value))
        }
        // Missing raw arguments stay explicit, never relabel the validated arguments as raw.
        add(DebugSection("$index-raw", "$title · Raw parameters", call.rawParameters ?: JsonNull))
        section("validated", "Validated parameters", call.validatedParameters ?: call.parameters)
        section("merged", "Merged parameters", call.mergedParameters)
        section("validation", "Validation", call.validation)
        section("data", "Returned data", call.data)
        section("model", "Model", call.model)
        section("renderer", "Renderer", call.renderer)
        section("before", "Context before", call.contextBefore)
        section("after", "Context after", call.contextAfter)
    }
    val metrics = buildJsonObject {
        put("latency_ms", response.debug["latency_ms"] ?: response.latencyMs?.let(::JsonPrimitive) ?: JsonNull)
        put("attempts", response.debug["attempts"] ?: response.attempts?.let(::JsonPrimitive) ?: JsonNull)
        put("llm_called", response.debug["llm_called"] ?: response.llmCalled?.let(::JsonPrimitive) ?: JsonNull)
    }
    add(DebugSection("execution", "Execution", metrics))
    (response.debug["retrieval"] ?: response.retrieval)?.takeUnless { it == JsonNull }?.let {
        add(DebugSection("retrieval", "Retrieval", it))
    }
}
