package com.serie76.assistant.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.KSerializer
import kotlinx.serialization.descriptors.PrimitiveKind
import kotlinx.serialization.descriptors.PrimitiveSerialDescriptor
import kotlinx.serialization.encoding.Decoder
import kotlinx.serialization.encoding.Encoder
import kotlinx.serialization.json.JsonDecoder
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.intOrNull
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
    val lead: String? = null,
    val interaction: Interaction? = null,
    val suggestions: List<String>? = null,
    @SerialName("active_filters") val activeFilters: List<ActiveFilter> = emptyList(),
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
    val answers: Map<String, String> = emptyMap(),
    @SerialName("remove_filters") val removeFilters: List<String> = emptyList(),
)

@Serializable
data class ConversationResponse(
    @SerialName("session_id") val sessionId: String,
    val answer: String,
    @SerialName("message_id") val messageId: String,
    val products: List<Product> = emptyList(),
    @SerialName("suggested_replies") val suggestedReplies: List<String> = emptyList(),
    val comparison: DifferenceComparison? = null,
    val lead: String? = null,
    val interaction: Interaction? = null,
    val suggestions: List<String>? = null,
    @SerialName("active_filters") val activeFilters: List<ActiveFilter> = emptyList(),
)

@Serializable
data class Interaction(val kind: String = "question", val questions: List<Question> = emptyList())

@Serializable
data class Question(val id: String, val prompt: String, val options: List<QuestionOption>)

@Serializable
data class QuestionOption(val value: String, val label: String)

@Serializable
data class ActiveFilter(val field: String, val label: String)

/** Legacy persisted comparisons used a/b strings for values and direction. */
object BetterIndexSerializer : KSerializer<Int> {
    override val descriptor = PrimitiveSerialDescriptor("BetterIndex", PrimitiveKind.INT)
    override fun deserialize(decoder: Decoder): Int {
        val value = (decoder as JsonDecoder).decodeJsonElement().jsonPrimitive
        return value.intOrNull ?: when (value.content) {
            "a" -> 0
            "b" -> 1
            else -> error("Invalid comparison direction")
        }
    }
    override fun serialize(encoder: Encoder, value: Int) = encoder.encodeInt(value)
}

@Serializable
data class DifferenceRow(
    val field: String, val label: String, val a: String = "", val b: String = "",
    @Serializable(with = BetterIndexSerializer::class) val better: Int? = null,
    val values: List<String> = emptyList(),
) {
    val displayValues: List<String> get() = values.ifEmpty { listOf(a, b) }
}

@Serializable
data class DifferenceComparison(
    val models: List<String>, val rows: List<DifferenceRow>,
    @SerialName("identical_fields_hidden") val identicalFieldsHidden: Int = 0,
    val layout: String = "table",
    val summary: String = "",
    val assumptions: String = "",
    @SerialName("hidden_rows") val hiddenRows: List<DifferenceRow> = emptyList(),
    @SerialName("key_fields") val keyFields: List<String> = emptyList(),
)

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
