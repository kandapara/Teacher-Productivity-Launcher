package com.teacher.productivitylauncher.presentation.settings

import android.content.Intent
import android.provider.Settings
import android.widget.Toast
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(onClose: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Fix: Move isSystemInDarkTheme() outside remember
    val isDarkTheme = isSystemInDarkTheme()
    var isDarkMode by remember { mutableStateOf(isDarkTheme) }
    var notificationsEnabled by remember { mutableStateOf(true) }

    val settingsItems = listOf(
        SettingsItem(
            id = "dark_mode",
            title = "Dark Mode",
            icon = Icons.Default.DarkMode,
            type = SettingsItemType.SWITCH,
            value = isDarkMode
        ),
        SettingsItem(
            id = "notifications",
            title = "Class Reminders",
            icon = Icons.Default.Notifications,
            type = SettingsItemType.SWITCH,
            value = notificationsEnabled
        ),
        SettingsItem(
            id = "backup",
            title = "Backup Data",
            icon = Icons.Default.Backup,
            type = SettingsItemType.BUTTON,
            onClick = {
                Toast.makeText(context, "Backup feature coming soon", Toast.LENGTH_SHORT).show()
            }
        ),
        SettingsItem(
            id = "restore",
            title = "Restore Data",
            icon = Icons.Default.Restore,
            type = SettingsItemType.BUTTON,
            onClick = {
                Toast.makeText(context, "Restore feature coming soon", Toast.LENGTH_SHORT).show()
            }
        ),
        SettingsItem(
            id = "default_launcher",
            title = "Set as Default Launcher",
            icon = Icons.Default.Home,
            type = SettingsItemType.BUTTON,
            onClick = {
                openDefaultLauncherSettings(context)
            }
        ),
        SettingsItem(
            id = "about",
            title = "About",
            icon = Icons.Default.Info,
            type = SettingsItemType.NAVIGATION,
            onClick = {
                Toast.makeText(context, "Version 1.0.0", Toast.LENGTH_SHORT).show()
            }
        )
    )

    ModalBottomSheet(
        onDismissRequest = onClose,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⚙️ Settings",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                IconButton(onClick = onClose) {
                    Icon(Icons.Default.Close, contentDescription = "Close")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(settingsItems) { item ->
                    when (item.type) {
                        SettingsItemType.SWITCH -> {
                            SettingsSwitchItem(
                                item = item,
                                onCheckedChange = { checked ->
                                    when (item.id) {
                                        "dark_mode" -> isDarkMode = checked
                                        "notifications" -> notificationsEnabled = checked
                                    }
                                }
                            )
                        }
                        SettingsItemType.BUTTON, SettingsItemType.NAVIGATION -> {
                            SettingsButtonItem(item = item)
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // App Version
            Text(
                text = "Version 1.0.0",
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(8.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}

@Composable
fun SettingsSwitchItem(
    item: SettingsItem,
    onCheckedChange: (Boolean) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    item.icon,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    item.title,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }
            Switch(
                checked = item.value as Boolean,
                onCheckedChange = onCheckedChange
            )
        }
    }
}

@Composable
fun SettingsButtonItem(item: SettingsItem) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { item.onClick?.invoke() },
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    item.icon,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    item.title,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }
            if (item.type == SettingsItemType.NAVIGATION) {
                Icon(
                    Icons.Default.ChevronRight,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                )
            }
        }
    }
}

fun openDefaultLauncherSettings(context: android.content.Context) {
    try {
        val intent = Intent(Settings.ACTION_HOME_SETTINGS)
        context.startActivity(intent)
    } catch (e: Exception) {
        Toast.makeText(context, "Cannot open launcher settings", Toast.LENGTH_SHORT).show()
    }
}

enum class SettingsItemType {
    SWITCH, BUTTON, NAVIGATION
}

data class SettingsItem(
    val id: String,
    val title: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val type: SettingsItemType,
    val value: Any = false,
    val onClick: (() -> Unit)? = null
)