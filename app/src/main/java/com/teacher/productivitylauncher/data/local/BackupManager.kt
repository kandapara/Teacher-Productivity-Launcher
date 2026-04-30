package com.teacher.productivitylauncher.data.local

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.core.content.FileProvider
import com.teacher.productivitylauncher.BuildConfig
import com.teacher.productivitylauncher.data.local.database.TeacherDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

class BackupManager(private val context: Context) {

    private val database = TeacherDatabase.getDatabase(context)

    suspend fun exportDatabase(): File? = withContext(Dispatchers.IO) {
        try {
            val students = database.studentDao().getAllStudents()
            val routines = database.classRoutineDao().getRoutineByClass("")
            val notes = database.noteDao().getAllNotes()
            val exams = database.examDao().getAllExams()

            val jsonObject = JSONObject().apply {
                put("export_date", SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date()))
                put("version", 1)

                // Students
                val studentsArray = JSONArray()
                students.collect { list ->
                    list.forEach { student ->
                        studentsArray.put(JSONObject().apply {
                            put("name", student.name)
                            put("className", student.className)
                            put("batch", student.batch)
                            put("phone", student.phone)
                            put("guardianName", student.guardianName)
                            put("guardianPhone", student.guardianPhone)
                            put("feesDue", student.feesDue)
                            put("joinDate", student.joinDate.time)
                        })
                    }
                }
                put("students", studentsArray)

                // Notes
                val notesArray = JSONArray()
                notes.collect { list ->
                    list.forEach { note ->
                        notesArray.put(JSONObject().apply {
                            put("title", note.title)
                            put("content", note.content)
                            put("createdDate", note.createdDate.time)
                            put("isPinned", note.isPinned)
                        })
                    }
                }
                put("notes", notesArray)

                // Exams
                val examsArray = JSONArray()
                exams.collect { list ->
                    list.forEach { exam ->
                        examsArray.put(JSONObject().apply {
                            put("examName", exam.examName)
                            put("className", exam.className)
                            put("examDate", exam.examDate.time)
                            put("description", exam.description ?: "")
                        })
                    }
                }
                put("exams", examsArray)
            }

            val backupFile = File(context.filesDir, "backup_${System.currentTimeMillis()}.json")
            FileOutputStream(backupFile).use { outputStream ->
                outputStream.write(jsonObject.toString().toByteArray())
            }

            backupFile
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    fun shareBackupFile(file: File) {
        try {
            val authority = "${context.packageName}.fileprovider"
            val uri = FileProvider.getUriForFile(
                context,
                authority,
                file
            )
            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/json"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(shareIntent, "Share Backup"))
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(context, "Error sharing backup: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
}