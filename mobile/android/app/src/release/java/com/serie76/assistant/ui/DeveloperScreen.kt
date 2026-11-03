package com.serie76.assistant.ui

import androidx.compose.runtime.Composable

// No endpoint, control or screen implementation is packaged in the release source set.
@Composable fun DeveloperEntry(onOpen: () -> Unit) = Unit
@Composable fun DeveloperScreen(state: AppState, onBack: () -> Unit, onChoose: (String) -> Unit) = Unit
