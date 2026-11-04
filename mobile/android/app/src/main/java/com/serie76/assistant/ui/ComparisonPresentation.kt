package com.serie76.assistant.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.CollectionInfo
import androidx.compose.ui.semantics.collectionInfo
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.serie76.assistant.data.DifferenceComparison

@Composable
fun DifferenceComparisonCard(comparison: DifferenceComparison) {
    if (comparison.layout == "cards") ModelComparisonCards(comparison) else ComparisonDifferenceTable(comparison)
}

@Composable
private fun ComparisonDifferenceTable(comparison: DifferenceComparison) {
    var expanded by rememberSaveable(comparison) { mutableStateOf(false) }
    val rows = comparison.visibleRows(expanded)
    val arrowColor = if (LocalAppearance.current.dark) Color(0xFFFFB66D) else Color(0xFFAD5100)
    OutlinedCard(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            ComparisonSummary(comparison)
            Column(Modifier.semantics { collectionInfo = CollectionInfo(rows.size + 1, 3) },
                verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Field", Modifier.weight(0.9f), style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                    comparison.models.take(2).forEach { code ->
                        Text(comparisonModelTitle(code), Modifier.weight(1f), style = MaterialTheme.typography.labelMedium)
                    }
                }
                rows.forEach { row ->
                    HorizontalDivider()
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(row.label, Modifier.weight(0.9f), style = MaterialTheme.typography.bodySmall)
                        comparison.models.take(2).indices.forEach { index ->
                            val better = row.better == index
                            Text(buildAnnotatedString {
                                append(row.displayValues.getOrElse(index) { "Not reported" })
                                if (better) withStyle(SpanStyle(color = arrowColor)) { append(" ↑") }
                            }, Modifier.weight(1f), style = MaterialTheme.typography.bodySmall,
                                fontWeight = if (better) FontWeight.Bold else FontWeight.Normal)
                        }
                    }
                }
            }
            val hidden = comparison.hiddenRows.size.takeIf { it > 0 } ?: comparison.identicalFieldsHidden
            if (comparison.hiddenRows.isNotEmpty()) {
                TextButton(onClick = { expanded = !expanded }) {
                    Text(if (expanded) "$hidden identical fields · Hide" else "$hidden identical fields hidden · Show",
                        style = MaterialTheme.typography.labelSmall)
                }
            } else if (hidden > 0) Text("$hidden identical fields hidden", style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
private fun ModelComparisonCards(comparison: DifferenceComparison) {
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        ComparisonSummary(comparison)
        if (comparison.keyFieldsReason.isNotBlank()) Text(comparison.keyFieldsReason,
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        comparison.models.forEachIndexed { index, code ->
            OutlinedCard(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(code, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                    comparison.cardFields(index).chunked(2).forEach { pair ->
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            pair.forEach { (label, value) ->
                                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                    Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Text(value, style = MaterialTheme.typography.titleMedium)
                                }
                            }
                            if (pair.size == 1) Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ComparisonSummary(comparison: DifferenceComparison) {
    if (comparison.summary.isNotBlank()) Text(comparison.summary, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
    if (comparison.assumptions.isNotBlank()) Text(comparison.assumptions, style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant)
}
