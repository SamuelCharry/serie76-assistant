package com.serie76.assistant.ui

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

// A simple geometric icon avoids adding the entire extended Material icon package.
val SendUp: ImageVector by lazy {
    ImageVector.Builder("SendUp", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 2f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round) {
            moveTo(12f, 19f); lineTo(12f, 5f)
            moveTo(5f, 12f); lineTo(12f, 5f); lineTo(19f, 12f)
        }
    }.build()
}
