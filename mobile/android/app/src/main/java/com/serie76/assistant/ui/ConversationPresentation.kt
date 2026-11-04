package com.serie76.assistant.ui

import com.serie76.assistant.data.*

/** Pure state machine: selections stay local until the explicit review Submit. */
data class QuestionStepper(
    val questions: List<Question>,
    val index: Int = 0,
    val answers: Map<String, String> = emptyMap(),
) {
    val reviewing: Boolean get() = questions.isNotEmpty() && index == questions.size
    val current: Question? get() = questions.getOrNull(index)
    val reviewLines: List<String> get() = questions.map { "${it.prompt} → ${label(it)}" }

    private fun label(question: Question): String = question.options.firstOrNull { it.value == answers[question.id] }?.label.orEmpty()

    fun choose(value: String): QuestionStepper {
        val question = current ?: return this
        if (question.options.none { it.value == value }) return this
        val updated = answers + (question.id to value)
        return copy(answers = answers + (question.id to value))
    }

    fun next(): QuestionStepper = if (current != null && answers.containsKey(current!!.id)) copy(index = index + 1) else this
    fun back(): QuestionStepper = if (index > 0) copy(index = index - 1) else this

    fun edit(step: Int): QuestionStepper = if (reviewing && step in questions.indices) copy(index = step) else this

    fun submission(sessionId: String?): ConversationRequest? {
        if (!reviewing || questions.any { q -> q.options.none { it.value == answers[q.id] } }) return null
        return ConversationRequest(questions.joinToString(" · ", transform = ::label), sessionId, answers)
    }
}

fun cancelQuestionRequest(sessionId: String?) = ConversationRequest("Cancel", sessionId)
fun removeFilterRequest(filter: ActiveFilter, sessionId: String?) =
    ConversationRequest("Remove ${filter.label}", sessionId, removeFilters = listOf(filter.field))

fun visibleSuggestions(message: Message, draft: String, dismissed: Boolean): List<Suggestion> =
    if (message.interaction != null || draft.isNotEmpty() || dismissed) emptyList()
    else (message.suggestions ?: message.suggestedReplies.map(::Suggestion)).take(3)

fun suggestionRequest(suggestion: Suggestion, sessionId: String?) =
    ConversationRequest(suggestion.label, sessionId, action = suggestion.action)

fun Message.displayText(): String = if (comparison != null || products.isNotEmpty()) lead ?: content else content

fun DifferenceComparison.visibleRows(expanded: Boolean): List<DifferenceRow> = rows + if (expanded) hiddenRows else emptyList()

fun DifferenceComparison.cardFields(modelIndex: Int): List<Pair<String, String>> = keyFields.take(4).mapNotNull { field ->
    rows.firstOrNull { it.field == field }?.let { it.label to it.displayValues.getOrElse(modelIndex) { "Not reported" } }
}

fun comparisonModelTitle(code: String): String = if (code.length > 12 && '-' in code) code.replaceFirst("-", "\n-") else code

fun greeting(name: String?): String = name?.trim()?.split(Regex("\\s+"))?.firstOrNull()?.takeIf { it.isNotBlank() }
    ?.let { "Hello, $it" } ?: "Hello"
