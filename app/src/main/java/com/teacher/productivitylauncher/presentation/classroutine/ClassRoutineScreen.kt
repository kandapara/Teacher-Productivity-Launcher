package com.teacher.productivitylauncher.presentation.classroutine

import android.app.Application
import androidx.compose.foundation.clickable
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
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.teacher.productivitylauncher.data.local.entity.ClassRoutine
import java.util.*

class ClassRoutineViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ClassRoutineViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ClassRoutineViewModel(application) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

val days = listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClassRoutineScreen(onClose: () -> Unit) {
    val context = LocalContext.current
    val viewModel: ClassRoutineViewModel = viewModel(
        factory = ClassRoutineViewModelFactory(context.applicationContext as Application)
    )

    val routines by viewModel.routines.collectAsState()
    val availableClasses by viewModel.availableClasses.collectAsState()
    val selectedClass by viewModel.selectedClass.collectAsState()
    val message by viewModel.message.collectAsState()

    var showAddDialog by remember { mutableStateOf(false) }
    var selectedRoutine by remember { mutableStateOf<ClassRoutine?>(null) }
    var showClassSelector by remember { mutableStateOf(false) }

    // Load routines when class changes
    LaunchedEffect(selectedClass) {
        if (selectedClass.isNotEmpty()) {
            viewModel.loadRoutinesByClass(selectedClass)
        }
    }

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
                    text = "📚 Class Routine",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                Row {
                    IconButton(onClick = { showAddDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "Add Class")
                    }
                    IconButton(onClick = onClose) {
                        Icon(Icons.Default.Close, contentDescription = "Close")
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Class selector
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { showClassSelector = true },
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(if (selectedClass.isEmpty()) "Select Class" else "Class: $selectedClass")
                    Icon(Icons.Default.ArrowDropDown, contentDescription = null)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Message
            if (message.isNotEmpty()) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Text(message, modifier = Modifier.padding(8.dp), fontSize = 12.sp)
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            // Routine list by day
            if (selectedClass.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text("Select a class to view routine", fontSize = 12.sp)
                }
            } else if (routines.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.Schedule, contentDescription = null, modifier = Modifier.size(48.dp))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("No classes scheduled")
                        Text("Tap + to add a class", fontSize = 12.sp)
                    }
                }
            } else {
                LazyColumn {
                    val groupedByDay = routines.groupBy { it.dayOfWeek }
                    days.forEachIndexed { index, day ->
                        val dayRoutines = groupedByDay[index + 1] ?: emptyList()
                        if (dayRoutines.isNotEmpty()) {
                            item {
                                Text(
                                    text = day,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    modifier = Modifier.padding(vertical = 8.dp),
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                            items(dayRoutines) { routine ->
                                RoutineItem(
                                    routine = routine,
                                    onEdit = { selectedRoutine = routine },
                                    onDelete = { viewModel.deleteRoutine(it) },
                                    onToggleNotification = { viewModel.toggleNotification(it) }
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                            }
                        }
                    }
                }
            }
        }
    }

    // Class selector dialog
    if (showClassSelector) {
        AlertDialog(
            onDismissRequest = { showClassSelector = false },
            title = { Text("Select Class") },
            text = {
                Column {
                    availableClasses.forEach { className ->
                        TextButton(
                            onClick = {
                                viewModel.loadRoutinesByClass(className)
                                showClassSelector = false
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(className)
                        }
                    }
                    if (availableClasses.isEmpty()) {
                        Text("No classes added yet", fontSize = 12.sp)
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showClassSelector = false }) {
                    Text("Cancel")
                }
            }
        )
    }

    // Add/Edit dialog
    if (showAddDialog || selectedRoutine != null) {
        RoutineDialog(
            routine = selectedRoutine,
            onDismiss = {
                showAddDialog = false
                selectedRoutine = null
            },
            onSave = { subjectName, className, teacherName, dayOfWeek, startTime, endTime, roomNumber ->
                if (selectedRoutine != null) {
                    val updated = selectedRoutine!!.copy(
                        subjectName = subjectName,
                        className = className,
                        teacherName = teacherName,
                        dayOfWeek = dayOfWeek,
                        startTime = startTime,
                        endTime = endTime,
                        roomNumber = roomNumber
                    )
                    viewModel.updateRoutine(updated)
                } else {
                    viewModel.addRoutine(subjectName, className, teacherName, dayOfWeek, startTime, endTime, roomNumber)
                }
                showAddDialog = false
                selectedRoutine = null
            }
        )
    }
}

@Composable
fun RoutineItem(
    routine: ClassRoutine,
    onEdit: () -> Unit,
    onDelete: (ClassRoutine) -> Unit,
    onToggleNotification: (ClassRoutine) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(routine.subjectName, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Text("Teacher: ${routine.teacherName}", fontSize = 12.sp)
                    Text("Time: ${routine.startTime} - ${routine.endTime}", fontSize = 12.sp)
                    Text("Room: ${routine.roomNumber}", fontSize = 12.sp)
                }
                Column(horizontalAlignment = Alignment.End) {
                    IconButton(onClick = { onToggleNotification(routine) }) {
                        Icon(
                            if (routine.notificationEnabled) Icons.Default.Notifications else Icons.Default.NotificationsOff,
                            contentDescription = "Notifications",
                            modifier = Modifier.size(20.dp)
                        )
                    }
                    Row {
                        IconButton(onClick = onEdit) {
                            Icon(Icons.Default.Edit, contentDescription = "Edit", modifier = Modifier.size(20.dp))
                        }
                        IconButton(onClick = { onDelete(routine) }) {
                            Icon(Icons.Default.Delete, contentDescription = "Delete", modifier = Modifier.size(20.dp))
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RoutineDialog(
    routine: ClassRoutine?,
    onDismiss: () -> Unit,
    onSave: (subjectName: String, className: String, teacherName: String,
             dayOfWeek: Int, startTime: String, endTime: String, roomNumber: String) -> Unit
) {
    var subjectName by remember { mutableStateOf(routine?.subjectName ?: "") }
    var className by remember { mutableStateOf(routine?.className ?: "") }
    var teacherName by remember { mutableStateOf(routine?.teacherName ?: "") }
    var selectedDay by remember { mutableStateOf(routine?.dayOfWeek ?: 1) }
    var startTime by remember { mutableStateOf(routine?.startTime ?: "09:00 AM") }
    var endTime by remember { mutableStateOf(routine?.endTime ?: "10:00 AM") }
    var roomNumber by remember { mutableStateOf(routine?.roomNumber ?: "") }

    var dayExpanded by remember { mutableStateOf(false) }
    var startTimeExpanded by remember { mutableStateOf(false) }
    var endTimeExpanded by remember { mutableStateOf(false) }

    val timeSlots = listOf(
        "08:00 AM", "08:30 AM", "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
        "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM",
        "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
        "05:00 PM"
    )

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (routine == null) "Add Class" else "Edit Class") },
        text = {
            Column {
                OutlinedTextField(
                    value = subjectName,
                    onValueChange = { subjectName = it },
                    label = { Text("Subject Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = className,
                    onValueChange = { className = it },
                    label = { Text("Class (e.g., Class 8)") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = teacherName,
                    onValueChange = { teacherName = it },
                    label = { Text("Teacher Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))

                // Day selection
                ExposedDropdownMenuBox(
                    expanded = dayExpanded,
                    onExpandedChange = { dayExpanded = it }
                ) {
                    OutlinedTextField(
                        value = days[selectedDay - 1],
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Day") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = dayExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    DropdownMenu(
                        expanded = dayExpanded,
                        onDismissRequest = { dayExpanded = false }
                    ) {
                        days.forEachIndexed { index, day ->
                            DropdownMenuItem(
                                text = { Text(day) },
                                onClick = {
                                    selectedDay = index + 1
                                    dayExpanded = false
                                }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Start Time
                ExposedDropdownMenuBox(
                    expanded = startTimeExpanded,
                    onExpandedChange = { startTimeExpanded = it }
                ) {
                    OutlinedTextField(
                        value = startTime,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Start Time") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = startTimeExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    DropdownMenu(
                        expanded = startTimeExpanded,
                        onDismissRequest = { startTimeExpanded = false }
                    ) {
                        timeSlots.forEach { time ->
                            DropdownMenuItem(
                                text = { Text(time) },
                                onClick = {
                                    startTime = time
                                    startTimeExpanded = false
                                }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // End Time
                ExposedDropdownMenuBox(
                    expanded = endTimeExpanded,
                    onExpandedChange = { endTimeExpanded = it }
                ) {
                    OutlinedTextField(
                        value = endTime,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("End Time") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = endTimeExpanded) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    DropdownMenu(
                        expanded = endTimeExpanded,
                        onDismissRequest = { endTimeExpanded = false }
                    ) {
                        timeSlots.forEach { time ->
                            DropdownMenuItem(
                                text = { Text(time) },
                                onClick = {
                                    endTime = time
                                    endTimeExpanded = false
                                }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                OutlinedTextField(
                    value = roomNumber,
                    onValueChange = { roomNumber = it },
                    label = { Text("Room Number") },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (subjectName.isNotBlank() && className.isNotBlank() && teacherName.isNotBlank()) {
                        onSave(subjectName, className, teacherName, selectedDay, startTime, endTime, roomNumber)
                    }
                }
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}