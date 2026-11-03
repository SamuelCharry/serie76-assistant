package com.serie76.assistant.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

@Serializable
data class Session(
    val id: String,
    val title: String,
    @SerialName("updated_at") val updatedAt: String,
    val preview: String = "",
)

@Serializable
data class SessionsPage(val sessions: List<Session>, val limit: Int = 50, val offset: Int = 0)

@Serializable
data class Message(
    val id: String,
    val role: String,
    val content: String,
    val products: List<Product> = emptyList(),
    @SerialName("created_at") val createdAt: String = "",
    val sequence: Long = 0,
    @SerialName("suggested_replies") val suggestedReplies: List<String> = emptyList(),
    val comparison: DifferenceComparison? = null,
)

@Serializable
data class MessagesPage(
    @SerialName("session_id") val sessionId: String,
    val title: String,
    val messages: List<Message>,
    @SerialName("has_more") val hasMore: Boolean = false,
    @SerialName("next_before") val nextBefore: Long? = null,
)

@Serializable
data class ConversationRequest(
    val query: String,
    @SerialName("session_id") val sessionId: String? = null,
)

@Serializable
data class ConversationResponse(
    @SerialName("session_id") val sessionId: String,
    val answer: String,
    @SerialName("message_id") val messageId: String,
    val products: List<Product> = emptyList(),
    @SerialName("suggested_replies") val suggestedReplies: List<String> = emptyList(),
    val comparison: DifferenceComparison? = null,
)

@Serializable
data class DifferenceRow(val field: String, val label: String, val a: String, val b: String, val better: String? = null) {
    init { require(better == null || better == "a" || better == "b") }
}

@Serializable
data class DifferenceComparison(
    val models: List<String>, val rows: List<DifferenceRow>,
    @SerialName("identical_fields_hidden") val identicalFieldsHidden: Int = 0,
) {
    init { require(models.size == 2) }
}

@Serializable
data class Product(
    @SerialName("base_part_number") val partNumber: String,
    val enclosure: String = "",
    @SerialName("supply_voltage_v") val voltage: JsonPrimitive? = null,
    @SerialName("supply_current") val current: String = "",
    @SerialName("phase_count") val phases: Int? = null,
    @SerialName("data_status") val dataStatus: String = "",
    @SerialName("service_layout") val serviceLayout: String = "",
    val measurements: Map<String, JsonElement?> = emptyMap(),
    @SerialName("field_status") val fieldStatus: Map<String, String> = emptyMap(),
    val certification: JsonObject = JsonObject(emptyMap()),
    val notes: List<JsonObject> = emptyList(),
    val source: ProductSource = ProductSource(),
)

@Serializable
data class ProductSource(val document: String = "", val page: Int? = null, val table: String? = null)

@Serializable
data class ToolCall(val name: String, val parameters: JsonElement, val data: JsonElement)

@Serializable
data class DebugResponse(
    @SerialName("message_id") val messageId: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("tool_calls") val toolCalls: List<ToolCall>,
)
