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

val ArrowNorthEast: ImageVector by lazy {
    ImageVector.Builder("ArrowNorthEast", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.6f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round) {
            moveTo(5f, 19f); lineTo(19f, 5f)
            moveTo(6f, 5f); lineTo(19f, 5f); lineTo(19f, 18f)
        }
    }.build()
}

val MenuLines: ImageVector by lazy {
    ImageVector.Builder("MenuLines", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.7f, strokeLineCap = StrokeCap.Round) {
            moveTo(4f, 6f); lineTo(20f, 6f)
            moveTo(4f, 12f); lineTo(20f, 12f)
            moveTo(4f, 18f); lineTo(20f, 18f)
        }
    }.build()
}

val CloseLines: ImageVector by lazy {
    ImageVector.Builder("CloseLines", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.7f, strokeLineCap = StrokeCap.Round) {
            moveTo(6f, 6f); lineTo(18f, 18f)
            moveTo(18f, 6f); lineTo(6f, 18f)
        }
    }.build()
}

val EditLines: ImageVector by lazy {
    ImageVector.Builder("EditLines", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.7f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round) {
            moveTo(12f, 4f); lineTo(5f, 4f); lineTo(5f, 20f); lineTo(20f, 20f); lineTo(20f, 13f)
            moveTo(10f, 14f); lineTo(11f, 10f); lineTo(19f, 2f); lineTo(22f, 5f); lineTo(14f, 13f); close()
            moveTo(17f, 4f); lineTo(20f, 7f)
        }
    }.build()
}

val HistoryLines: ImageVector by lazy {
    ImageVector.Builder("HistoryLines", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.4f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round) {
            moveTo(4f, 3f); lineTo(20f, 3f); lineTo(20f, 17f); lineTo(10f, 17f); lineTo(4f, 21f); close()
            moveTo(8f, 8f); lineTo(16f, 8f)
            moveTo(8f, 12f); lineTo(13f, 12f)
        }
    }.build()
}

val ProfileLines: ImageVector by lazy {
    ImageVector.Builder("ProfileLines", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.6f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round) {
            moveTo(16f, 8f)
            curveTo(16f, 10.2f, 14.2f, 12f, 12f, 12f)
            curveTo(9.8f, 12f, 8f, 10.2f, 8f, 8f)
            curveTo(8f, 5.8f, 9.8f, 4f, 12f, 4f)
            curveTo(14.2f, 4f, 16f, 5.8f, 16f, 8f)
            moveTo(4f, 21f)
            curveTo(4f, 16.6f, 7.6f, 14f, 12f, 14f)
            curveTo(16.4f, 14f, 20f, 16.6f, 20f, 21f)
        }
    }.build()
}
