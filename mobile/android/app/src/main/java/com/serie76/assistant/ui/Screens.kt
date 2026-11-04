@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class, androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package com.serie76.assistant.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.CollectionInfo
import androidx.compose.ui.semantics.collectionInfo
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.serie76.assistant.BuildConfig
import com.serie76.assistant.data.*
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlinx.coroutines.flow.drop

@Composable
fun SeriesApp(viewModel: AppViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val drawer = rememberDrawerState(DrawerValue.Closed)
    val keyboard = LocalSoftwareKeyboardController.current
    val latestScreen by rememberUpdatedState(state.screen)
    LaunchedEffect(state.screen) {
        if (state.screen == "sessions") { keyboard?.hide(); drawer.open() } else drawer.close()
    }
    LaunchedEffect(drawer) {
        // Scrim, swipe and native Back update the same persisted navigation state.
        snapshotFlow { drawer.currentValue }.drop(1).collect { value ->
            if (value == DrawerValue.Open && latestScreen == "chat") viewModel.showConversations()
            if (value == DrawerValue.Closed && latestScreen == "sessions") viewModel.dismissConversations()
        }
    }
    BackHandler(state.screen == "debug") { viewModel.back() }
    BackHandler(state.screen == "sessions" || drawer.isOpen) { viewModel.dismissConversations() }
    ModalNavigationDrawer(
        drawerState = drawer, gesturesEnabled = state.screen != "debug",
        scrimColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.24f),
        drawerContent = {
            ModalDrawerSheet(modifier = Modifier.fillMaxWidth(0.84f),
                drawerContainerColor = MaterialTheme.colorScheme.background,
                drawerShape = RoundedCornerShape(topEnd = 24.dp, bottomEnd = 24.dp)) {
                ConversationsScreen(state, viewModel::newConversation, viewModel::open,
                    { viewModel.refreshSessions() }, { viewModel.refreshSessions(more = true) },
                    viewModel::dismissConversations, viewModel::debug)
            }
        }
    ) {
        // Drawer does not replace or recreate the chat; only debug changes surface.
        Crossfade(targetState = BuildConfig.DEBUG && state.screen == "debug",
            animationSpec = tween(180), label = "Screen transition") { debug ->
            if (debug) DeveloperScreen(state, viewModel::back, viewModel::debugMessage)
            else ChatScreen(state, viewModel::showConversations, viewModel::draft, viewModel::send,
                { viewModel.loadHistory() }, { viewModel.loadHistory(older = true) },
                viewModel::reconcile, viewModel::debug, viewModel::newConversation,
                viewModel::chooseAnswer, viewModel::editAnswer, viewModel::submitAnswers,
                viewModel::cancelQuestion, viewModel::activateComposer, viewModel::removeFilter)
        }
    }
}

@Composable
fun ConversationsScreen(state: AppState, onNew: () -> Unit, onOpen: (Session) -> Unit,
                        onRefresh: () -> Unit, onMore: () -> Unit, onClose: () -> Unit = {}, onDebug: () -> Unit = {}) {
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(horizontal = 20.dp)) {
        Row(Modifier.fillMaxWidth().padding(top = 8.dp, bottom = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Conversations", Modifier.weight(1f), style = MaterialTheme.typography.titleLarge)
            IconButton(onClick = onClose) { Icon(CloseLines, "Close conversation history") }
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Spacer(Modifier.height(24.dp))
        Surface(onClick = onNew, enabled = !state.sending, color = Color.Transparent,
            shape = RoundedCornerShape(14.dp), modifier = Modifier.fillMaxWidth().background(SoftAccent, RoundedCornerShape(14.dp))) {
            Row(Modifier.heightIn(min = 52.dp).padding(horizontal = 18.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(EditLines, null, Modifier.size(20.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
                Spacer(Modifier.width(10.dp))
                Text("New chat", Modifier.weight(1f), style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onPrimaryContainer)
                Icon(ArrowNorthEast, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
            }
        }
        Text("Recent", Modifier.padding(top = 28.dp, bottom = 12.dp).semantics { heading() },
            style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        LazyColumn(Modifier.weight(1f), contentPadding = PaddingValues(bottom = 16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            if (state.sessionsLoading) item { LoadingLine("Loading conversations") }
            state.sessionsError?.let { error -> item { ErrorPanel(error, "Try again", onRefresh) } }
            if (!state.sessionsLoading && state.sessionsError == null && state.sessions.isEmpty()) item {
                Column(Modifier.fillMaxWidth().padding(top = 28.dp, bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(HistoryLines, null, Modifier.size(28.dp), tint = MaterialTheme.colorScheme.primary)
                    Text("No conversations yet", style = MaterialTheme.typography.titleMedium)
                    Text("Start a chat. Your saved conversations will appear here.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            items(state.sessions, key = Session::id) { session ->
                Surface(onClick = { onOpen(session) }, enabled = !state.sending,
                    modifier = Modifier.fillMaxWidth().animateItem().semantics { selected = session.id == state.sessionId },
                    shape = RoundedCornerShape(12.dp),
                    color = if (session.id == state.sessionId) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.background) {
                    Column(Modifier.padding(horizontal = 12.dp, vertical = 14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(session.title, style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        Text(displayDate(session.updatedAt), style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            if (state.sessionsHaveMore) item { TextButton(onClick = onMore, enabled = !state.sessionsLoading) { Text("Load more conversations") } }
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
        ProfileMenu()
        DeveloperEntry(onDebug)
        Spacer(Modifier.height(12.dp))
    }
}

@Composable
fun ChatScreen(state: AppState, onBack: () -> Unit, onDraft: (String) -> Unit, onSend: () -> Unit,
               onReload: () -> Unit, onOlder: () -> Unit, onReconcile: () -> Unit, onDebug: () -> Unit, onNew: () -> Unit = {},
               onChoose: (String) -> Unit = {}, onEditAnswer: (Int) -> Unit = {}, onSubmitAnswers: () -> Unit = {},
               onCancelQuestion: () -> Unit = {}, onActivateComposer: () -> Unit = {}, onRemoveFilter: (ActiveFilter) -> Unit = {}) {
    val listState = rememberLazyListState()
    val focus = remember { FocusRequester() }
    val keyboard = LocalSoftwareKeyboardController.current
    val keyboardVisible = WindowInsets.ime.getBottom(LocalDensity.current) > 0
    LaunchedEffect(state.messages.lastOrNull()?.id, state.sending) {
        if (state.messages.isNotEmpty()) listState.animateScrollToItem((listState.layoutInfo.totalItemsCount - 1).coerceAtLeast(0))
    }
    Box(Modifier.fillMaxSize()) {
    ChatBackdrop(Modifier.fillMaxSize(), empty = state.screen == "chat" && state.messages.isEmpty() &&
        state.draft.isBlank() && !keyboardVisible && !state.sending && !state.historyLoading && state.historyError == null)
    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            Column {
            TopAppBar(title = { Text(if (state.messages.isEmpty() && state.sessionId == null) "" else state.title,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleLarge) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Transparent),
                navigationIcon = { IconButton(onClick = onBack) { Icon(MenuLines, "Open conversation history") } },
                actions = { IconButton(onClick = onNew, enabled = !state.sending) { Icon(EditLines, "New conversation") } })
            ActiveFilterTags(state.activeFilters, state.canSend, onRemoveFilter)
            }
        },
        bottomBar = {
            Surface(color = Color.Transparent) {
                Column(Modifier.navigationBarsPadding().imePadding().padding(horizontal = 16.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.sendError?.let { ErrorPanel(it, if (state.sessionId == null) "Check conversations" else "Reload conversation", onReconcile) }
                    if (state.needsReconcile && state.sendError == null) ErrorPanel("A previous request may have completed. Check saved messages before sending again.",
                        if (state.sessionId == null) "Check conversations" else "Reload conversation", onReconcile)
                    state.question?.let { QuestionCard(it, state.canSend, onChoose, onEditAnswer, onSubmitAnswers, onCancelQuestion,
                        Modifier.weight(1f, fill = false)) }
                    Surface(modifier = Modifier.alpha(if (state.question != null && !state.composerActive) 0.5f else 1f)
                        .pointerInput(onActivateComposer) {
                            awaitEachGesture {
                                awaitFirstDown(requireUnconsumed = false, pass = PointerEventPass.Initial)
                                onActivateComposer()
                            }
                        }, color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(24.dp),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                        Row(Modifier.fillMaxWidth().padding(start = 20.dp, end = 10.dp, top = 16.dp, bottom = 10.dp),
                            verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            BasicTextField(value = state.draft, onValueChange = onDraft, minLines = 2, maxLines = 5,
                                modifier = Modifier.weight(1f).focusRequester(focus).onFocusChanged { if (it.isFocused) onActivateComposer() }
                                    .semantics { contentDescription = "Message" },
                                textStyle = MaterialTheme.typography.bodyLarge.copy(color = MaterialTheme.colorScheme.onSurface),
                                cursorBrush = SolidColor(MaterialTheme.colorScheme.onPrimaryContainer), enabled = !state.sending,
                                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send), keyboardActions = KeyboardActions(onSend = { onSend() }),
                                decorationBox = { field ->
                                    Box { if (state.draft.isEmpty()) Text("Ask a question", style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant); field() }
                                })
                            FilledIconButton(onClick = onSend, enabled = state.draft.isNotBlank() && !state.sending && !state.historyLoading && state.historyError == null && !state.needsReconcile,
                                modifier = Modifier.size(48.dp).background(SoftAccent, CircleShape), colors = IconButtonDefaults.filledIconButtonColors(
                                    containerColor = Color.Transparent, contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                                    disabledContainerColor = Color.Transparent,
                                    disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f))) {
                                Icon(SendUp, "Send message")
                            }
                        }
                    }
                }
            }
        }
    ) { insets ->
        Box(Modifier.fillMaxSize().padding(insets)) {
          if (state.messages.isEmpty() && !state.sending && !state.historyLoading && state.historyError == null && !keyboardVisible) {
              HelloGreeting(Modifier.align(Alignment.Center).padding(horizontal = 24.dp), LocalAccount.current?.user?.name)
          }
          LazyColumn(Modifier.fillMaxSize(), state = listState,
            contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp), verticalArrangement = Arrangement.spacedBy(24.dp)) {
            if (state.historyBefore != null) item { TextButton(colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onPrimaryContainer), onClick = onOlder, enabled = !state.historyLoading) { Text("Load earlier messages") } }
            if (state.historyLoading) item { LoadingLine("Loading messages") }
            state.historyError?.let { item { ErrorPanel(it, "Try again", onReload) } }
            items(state.messages, key = Message::id) { message ->
                MessageContent(message)
                if (message.role == "assistant" && message.id == state.messages.lastOrNull()?.id) {
                    SuggestedReplyChips(visibleSuggestions(message, state.draft, state.suggestionsDismissed || state.sending),
                        enabled = state.canSend) { reply ->
                        onDraft(reply)
                        onSend()
                    }
                }
            }
            if (state.sending) item {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(state.draft.trim(), style = MaterialTheme.typography.bodyLarge)
                    ThinkingLabel()
                }
            }
          }
        }
    }
    }
}

@Composable
fun MessageContent(message: Message) {
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (message.role == "user") {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.CenterEnd) {
                Surface(modifier = Modifier.widthIn(max = 320.dp), color = MaterialTheme.colorScheme.surfaceVariant, shape = RoundedCornerShape(20.dp)) {
                    Text(message.content, Modifier.padding(16.dp), style = MaterialTheme.typography.bodyLarge)
                }
            }
        } else {
            Text("Assistant", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(message.displayText(), style = MaterialTheme.typography.bodyLarge)
        }
        if (message.comparison != null) DifferenceComparisonCard(message.comparison)
        else if (message.products.size == 1) ProductCard(message.products.first())
        else if (message.products.isNotEmpty()) ComparisonTable(message.products)
    }
}

@Composable
fun ProductCard(product: Product) {
    OutlinedCard(shape = RoundedCornerShape(16.dp), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(product.partNumber, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("${product.enclosure.replaceFirstChar { it.uppercase() }} · ${supply(product)}", style = MaterialTheme.typography.bodyMedium)
            if (product.dataStatus != "reported") Text("N/A in the supplied catalogue", color = MaterialTheme.colorScheme.error)
            relevantFields(listOf(product)).forEach { field ->
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text(field.label, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(measurement(product, field), Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                }
            }
            ProductNotes(product)
        }
    }
}

@Composable
fun ComparisonTable(products: List<Product>) {
    val fields = remember(products) { relevantFields(products) }
    val scale = LocalDensity.current.fontScale.coerceAtLeast(1f)
    val rowHeight = 76.dp * scale
    val headerHeight = 96.dp * scale
    val scroll = rememberScrollState()
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Compare actuators", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
        Text("Swipe across to compare. Attribute labels stay in place.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Surface(shape = MaterialTheme.shapes.medium, modifier = Modifier.semantics { collectionInfo = CollectionInfo(fields.size + 3, products.size + 1) }) {
            Row {
                Column(Modifier.width(148.dp * scale)) {
                    TableCell("Specification", headerHeight, true)
                    TableCell("Power supply", rowHeight, true)
                    TableCell("Enclosure", rowHeight, true)
                    fields.forEach { TableCell("${it.label} (${it.unit})", rowHeight, true) }
                }
                Row(Modifier.horizontalScroll(scroll)) {
                    products.forEach { product ->
                        Column(Modifier.width(216.dp * scale)) {
                            TableCell(product.partNumber, headerHeight, false, true)
                            TableCell(supply(product), rowHeight, false, accessibilityLabel = "${product.partNumber}, power supply: ${supply(product)}")
                            TableCell(product.enclosure.replaceFirstChar { it.uppercase() }, rowHeight, false,
                                accessibilityLabel = "${product.partNumber}, enclosure: ${product.enclosure}")
                            fields.forEach { field -> TableCell(measurement(product, field), rowHeight, false,
                                accessibilityLabel = "${product.partNumber}, ${field.label}: ${measurement(product, field)}") }
                        }
                    }
                }
            }
        }
        products.forEach { product ->
            Column {
                Text(product.partNumber, style = MaterialTheme.typography.labelLarge)
                ProductNotes(product)
            }
        }
    }
}

@Composable
private fun TableCell(text: String, height: androidx.compose.ui.unit.Dp, label: Boolean, heading: Boolean = false, accessibilityLabel: String? = null) {
    val semantics = if (accessibilityLabel == null) Modifier else Modifier.clearAndSetSemantics { contentDescription = accessibilityLabel }
    Column(Modifier.fillMaxWidth().height(height).then(semantics).background(if (label) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface)) {
        Box(Modifier.weight(1f).padding(12.dp), contentAlignment = Alignment.CenterStart) {
            Text(text, style = MaterialTheme.typography.bodyMedium, fontWeight = if (heading) FontWeight.SemiBold else FontWeight.Normal)
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
    }
}

@Composable
private fun ProductNotes(product: Product) {
    var expanded by rememberSaveable(product.partNumber) { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Source: ${product.source.document}, page ${product.source.page ?: "not reported"}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        TextButton(colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onPrimaryContainer), onClick = { expanded = !expanded }) { Text(if (expanded) "Hide source notes" else "Source notes & exceptions") }
        if (expanded) fieldNotes(product).forEach { Text(it, style = MaterialTheme.typography.bodySmall) }
    }
}

@Composable
fun ErrorPanel(message: String, action: String, onAction: () -> Unit, modifier: Modifier = Modifier) {
    Surface(modifier, color = MaterialTheme.colorScheme.errorContainer, shape = MaterialTheme.shapes.medium) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(message, color = MaterialTheme.colorScheme.onErrorContainer, style = MaterialTheme.typography.bodyMedium)
            TextButton(colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onPrimaryContainer), onClick = onAction) { Text(action) }
        }
    }
}

@Composable
fun LoadingLine(label: String) {
    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimaryContainer)
        Text(label, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun EmptyState(title: String, body: String) {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Medium)
        Text(body, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

private fun displayDate(raw: String): String = try {
    val date = OffsetDateTime.parse(raw)
    val pattern = if (date.year == java.time.Year.now().value) "MMM d" else "MMM d, yyyy"
    date.format(DateTimeFormatter.ofPattern(pattern, Locale.ENGLISH))
} catch (_: Exception) { raw.take(10) }
