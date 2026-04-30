package com.teacher.productivitylauncher.presentation.classroutine

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.teacher.productivitylauncher.R
import com.teacher.productivitylauncher.data.local.database.TeacherDatabase
import com.teacher.productivitylauncher.data.local.entity.ClassRoutine
import com.teacher.productivitylauncher.data.local.repository.ClassRoutineRepository
import com.teacher.productivitylauncher.presentation.MainActivity
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.*

class ClassRoutineViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = ClassRoutineRepository(
        TeacherDatabase.getDatabase(application).classRoutineDao()
    )

    private val _routines = MutableStateFlow<List<ClassRoutine>>(emptyList())
    val routines: StateFlow<List<ClassRoutine>> = _routines.asStateFlow()

    private val _todayRoutines = MutableStateFlow<List<ClassRoutine>>(emptyList())
    val todayRoutines: StateFlow<List<ClassRoutine>> = _todayRoutines.asStateFlow()

    private val _selectedClass = MutableStateFlow("")
    val selectedClass: StateFlow<String> = _selectedClass.asStateFlow()

    private val _message = MutableStateFlow("")
    val message: StateFlow<String> = _message.asStateFlow()

    private val _availableClasses = MutableStateFlow<List<String>>(emptyList())
    val availableClasses: StateFlow<List<String>> = _availableClasses.asStateFlow()

    init {
        loadAvailableClasses()
        loadTodayRoutines()
    }

    private fun loadAvailableClasses() {
        viewModelScope.launch {
            val classes = repository.getDistinctClasses()
            _availableClasses.value = classes
        }
    }

    fun loadRoutinesByClass(className: String) {
        _selectedClass.value = className
        viewModelScope.launch {
            repository.getRoutineByClass(className).collect { routineList ->
                _routines.value = routineList
            }
        }
    }

    fun loadTodayRoutines() {
        val today = Calendar.getInstance().get(Calendar.DAY_OF_WEEK)
        val dayOfWeek = when (today) {
            Calendar.MONDAY -> 1
            Calendar.TUESDAY -> 2
            Calendar.WEDNESDAY -> 3
            Calendar.THURSDAY -> 4
            Calendar.FRIDAY -> 5
            Calendar.SATURDAY -> 6
            Calendar.SUNDAY -> 7
            else -> 1
        }

        viewModelScope.launch {
            if (_selectedClass.value.isEmpty()) {
                repository.getRoutineByDay(dayOfWeek).collect { routineList ->
                    _todayRoutines.value = routineList
                }
            } else {
                repository.getRoutineByDayAndClass(dayOfWeek, _selectedClass.value).collect { routineList ->
                    _todayRoutines.value = routineList
                }
            }
        }
    }

    fun addRoutine(subjectName: String, className: String, teacherName: String,
                   dayOfWeek: Int, startTime: String, endTime: String, roomNumber: String) {
        viewModelScope.launch {
            val routine = ClassRoutine(
                subjectName = subjectName,
                className = className,
                teacherName = teacherName,
                dayOfWeek = dayOfWeek,
                startTime = startTime,
                endTime = endTime,
                roomNumber = roomNumber,
                notificationEnabled = true
            )
            repository.insertRoutine(routine)
            _message.value = "Class added successfully"
            loadAvailableClasses()
            loadTodayRoutines()
            clearMessageAfterDelay()

            // Schedule notification for this class
            scheduleClassNotification(routine)
        }
    }

    fun updateRoutine(routine: ClassRoutine) {
        viewModelScope.launch {
            repository.updateRoutine(routine)
            _message.value = "Class updated successfully"
            loadTodayRoutines()
            clearMessageAfterDelay()
        }
    }

    fun deleteRoutine(routine: ClassRoutine) {
        viewModelScope.launch {
            repository.deleteRoutine(routine)
            _message.value = "Class deleted successfully"
            loadAvailableClasses()
            if (_selectedClass.value == routine.className) {
                loadRoutinesByClass(_selectedClass.value)
            }
            loadTodayRoutines()
            clearMessageAfterDelay()
        }
    }

    fun toggleNotification(routine: ClassRoutine) {
        viewModelScope.launch {
            val updated = routine.copy(notificationEnabled = !routine.notificationEnabled)
            repository.updateRoutine(updated)
            _message.value = if (updated.notificationEnabled) "Notifications enabled" else "Notifications disabled"
            clearMessageAfterDelay()
        }
    }

    private fun scheduleClassNotification(routine: ClassRoutine) {
        if (!routine.notificationEnabled) return

        val context = getApplication<Application>()

        // Create notification channel (Android 8+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                "class_reminder",
                "Class Reminders",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Reminders for upcoming classes"
                enableVibration(true)
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }

        showTestNotification(routine)
    }

    private fun showTestNotification(routine: ClassRoutine) {
        val context = getApplication<Application>()
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context, routine.id, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, "class_reminder")
            .setContentTitle("📚 Upcoming Class: ${routine.subjectName}")
            .setContentText("Time: ${routine.startTime} | Room: ${routine.roomNumber}")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(routine.id, notification)
    }

    private fun clearMessageAfterDelay() {
        viewModelScope.launch {
            kotlinx.coroutines.delay(2000)
            _message.value = ""
        }
    }

    fun clearMessage() {
        _message.value = ""
    }
}