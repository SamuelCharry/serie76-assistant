@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package com.serie76.assistant.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.serie76.assistant.data.ActiveFilter
import com.serie76.assistant.data.Suggestion

@Composable
fun QuestionCard(state: QuestionStepper, enabled: Boolean, onChoose: (String) -> Unit,
                 onEdit: (Int) -> Unit, onNext: () -> Unit, onBack: () -> Unit,
                 onSubmit: () -> Unit, onCancel: () -> Unit, error: String? = null, modifier: Modifier = Modifier) {
    OutlinedCard(modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(12.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("QUESTION", style = MaterialTheme.typography.labelSmall, letterSpacing = 1.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.semantics { heading() })
                Text(if (state.reviewing) "Review" else "${state.index + 1}/${state.questions.size}",
                    style = MaterialTheme.typography.labelSmall)
            }
            // Reserve header/actions first; scroll options when the keyboard reduces available height.
            Column(Modifier.weight(1f, fill = false).heightIn(max = 240.dp).verticalScroll(rememberScrollState()).selectableGroup()) {
                if (state.reviewing) {
                    state.reviewLines.forEachIndexed { index, line ->
                        Text(line, Modifier.fillMaxWidth().clickable(enabled = enabled, role = Role.Button,
                            onClickLabel = "Change answer") { onEdit(index) }.heightIn(min = 48.dp).padding(vertical = 12.dp),
                            style = MaterialTheme.typography.bodyMedium)
                    }
                } else state.current?.let { question ->
                    Text(question.prompt, Modifier.padding(top = 12.dp, bottom = 4.dp),
                        style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold)
                    state.optionRows.forEach { option ->
                        val selected = state.answers[question.id] == option.value
                        Row(Modifier.fillMaxWidth().selectable(selected = selected, enabled = enabled,
                            role = Role.RadioButton, onClick = { onChoose(option.value) }).heightIn(min = 48.dp).padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            RadioButton(selected = selected, onClick = null, enabled = enabled)
                            Column(Modifier.weight(1f)) {
                                Text(option.title, style = MaterialTheme.typography.bodyMedium)
                                option.description?.let { description ->
                                    Text(description, style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        maxLines = 3, overflow = TextOverflow.Ellipsis)
                                }
                            }
                        }
                    }
                }
            }
            if (state.reviewing && error != null) Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                TextButton(onClick = onCancel, enabled = enabled) { Text("Cancel") }
                if (state.index > 0) TextButton(onClick = onBack, enabled = enabled) { Text("Back") }
                if (!state.reviewing) TextButton(onClick = onNext,
                    enabled = enabled && state.current?.let { state.answers.containsKey(it.id) } == true) { Text("Next") }
                if (state.reviewing) Button(onClick = onSubmit, enabled = enabled) { Text("Submit") }
            }
        }
    }
}

@Composable
fun ActiveFilterTags(filters: List<ActiveFilter>, enabled: Boolean, onRemove: (ActiveFilter) -> Unit) {
    if (filters.isEmpty()) return
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        filters.forEach { filter ->
            InputChip(selected = false, enabled = enabled, onClick = { onRemove(filter) },
                label = { Text(filter.label) }, trailingIcon = { Text("×") },
                modifier = Modifier.semantics { contentDescription = "Remove ${filter.label}" })
        }
    }
}

@Composable
fun SuggestedReplyChips(replies: List<Suggestion>, enabled: Boolean, onReply: (Suggestion) -> Unit) {
    if (replies.isEmpty()) return
    val border = MaterialTheme.colorScheme.outline
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text("✦ Suggestions · optional", style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)) {
            replies.take(3).forEach { reply ->
                // Quiet visual chip with a full 48 dp accessible touch target.
                Box(Modifier.heightIn(min = 48.dp).clickable(enabled = enabled, role = Role.Button) { onReply(reply) },
                    contentAlignment = Alignment.Center) {
                    Surface(color = Color.Transparent, shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.drawWithContent {
                            drawContent()
                            val stroke = 1.dp.toPx()
                            drawRoundRect(border, Offset(stroke / 2, stroke / 2), Size(size.width - stroke, size.height - stroke),
                                CornerRadius(12.dp.toPx()), style = Stroke(stroke, pathEffect = PathEffect.dashPathEffect(floatArrayOf(4.dp.toPx(), 3.dp.toPx()))))
                        }) {
                        Text(reply.label, Modifier.padding(horizontal = 12.dp, vertical = 6.dp), style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}
