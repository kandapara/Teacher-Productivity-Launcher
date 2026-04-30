package com.teacher.productivitylauncher.presentation.appdrawer

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.teacher.productivitylauncher.data.local.AppInfo
import com.teacher.productivitylauncher.data.local.AppRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AppsDrawerViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = AppRepository(application)

    private val _apps = MutableStateFlow<List<AppInfo>>(emptyList())
    val apps: StateFlow<List<AppInfo>> = _apps.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _filteredApps = MutableStateFlow<List<AppInfo>>(emptyList())
    val filteredApps: StateFlow<List<AppInfo>> = _filteredApps.asStateFlow()

    init {
        loadApps()
    }

    fun loadApps() {
        viewModelScope.launch {
            repository.getInstalledApps().collect { appList ->
                _apps.value = appList
                filterApps()
            }
        }
    }

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
        filterApps()
    }

    private fun filterApps() {
        val query = _searchQuery.value.lowercase()
        if (query.isEmpty()) {
            _filteredApps.value = _apps.value
        } else {
            _filteredApps.value = _apps.value.filter { app ->
                app.name.lowercase().contains(query) ||
                        app.packageName.lowercase().contains(query)
            }
        }
    }

    fun openApp(app: AppInfo) {
        repository.openApp(getApplication(), app.packageName)
    }
}