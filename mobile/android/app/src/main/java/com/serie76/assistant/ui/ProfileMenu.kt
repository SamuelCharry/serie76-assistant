package com.serie76.assistant.ui

import android.content.Context
import android.util.Patterns
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

data class ProfileDetails(val name: String = "", val email: String = "")

/** Presentation details saved locally; this is not an authenticated account. */
@Composable
fun ProfileMenu() {
    val context = LocalContext.current
    val preferences = remember(context) { context.getSharedPreferences("profile", Context.MODE_PRIVATE) }
    var profile by remember(preferences) { mutableStateOf(ProfileDetails(
        preferences.getString("name", "").orEmpty(), preferences.getString("email", "").orEmpty())) }
    ProfileMenu(profile) { details ->
        preferences.edit().putString("name", details.name).putString("email", details.email).apply()
        profile = details
    }
}

@Composable
internal fun ProfileMenu(profile: ProfileDetails, onSave: (ProfileDetails) -> Unit) {
    val appearance = LocalAppearance.current
    var expanded by rememberSaveable { mutableStateOf(false) }
    var editing by rememberSaveable { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        Surface(onClick = { expanded = true }, shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.background,
            modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Open profile menu" }) {
            Row(Modifier.padding(vertical = 14.dp, horizontal = 4.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(Modifier.size(40.dp).background(SoftAccent, CircleShape), contentAlignment = Alignment.Center) {
                    Icon(ProfileLines, null, Modifier.size(20.dp), tint = MaterialTheme.colorScheme.onPrimaryContainer)
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(profile.name.ifBlank { "Profile" }, style = MaterialTheme.typography.titleSmall,
                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(profile.email.ifBlank { "Local profile" }, style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false },
            modifier = Modifier.widthIn(min = 240.dp, max = 300.dp), shape = RoundedCornerShape(16.dp),
            containerColor = MaterialTheme.colorScheme.surface, tonalElevation = 0.dp) {
            Column(Modifier.padding(horizontal = 16.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(profile.name.ifBlank { "Local profile" }, style = MaterialTheme.typography.titleMedium,
                    maxLines = 2, overflow = TextOverflow.Ellipsis)
                Text(profile.email.ifBlank { "No email added" }, style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text("Saved on this device", style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            DropdownMenuItem(text = { Text("Edit profile") }, onClick = { expanded = false; editing = true })
            HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
            Text("Appearance", Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            AppearanceMode.entries.forEach { mode ->
                DropdownMenuItem(text = { Text(mode.label) }, onClick = {
                    appearance.setMode(mode); expanded = false
                }, modifier = Modifier.semantics { selected = appearance.mode == mode },
                    trailingIcon = { RadioButton(selected = appearance.mode == mode, onClick = null) })
            }
        }
    }
    if (editing) ProfileEditor(profile, onDismiss = { editing = false }, onSave = {
        onSave(it); editing = false
    })
}

@Composable
private fun ProfileEditor(profile: ProfileDetails, onDismiss: () -> Unit, onSave: (ProfileDetails) -> Unit) {
    var name by rememberSaveable { mutableStateOf(profile.name) }
    var email by rememberSaveable { mutableStateOf(profile.email) }
    val validEmail = email.isBlank() || Patterns.EMAIL_ADDRESS.matcher(email.trim()).matches()
    AlertDialog(onDismissRequest = onDismiss, containerColor = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(24.dp), title = { Text("Edit profile") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("These details are saved on this device.", style = MaterialTheme.typography.bodyMedium)
            OutlinedTextField(value = name, onValueChange = { name = it.take(80) }, label = { Text("Name") },
                singleLine = true, modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Profile name" })
            OutlinedTextField(value = email, onValueChange = { email = it.take(254) }, label = { Text("Email") },
                singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                isError = !validEmail, supportingText = if (!validEmail) ({ Text("Enter a valid email address") }) else null,
                modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Profile email" })
        }
    }, confirmButton = { TextButton(enabled = validEmail, onClick = { onSave(ProfileDetails(name.trim(), email.trim())) }) { Text("Save") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } })
}
