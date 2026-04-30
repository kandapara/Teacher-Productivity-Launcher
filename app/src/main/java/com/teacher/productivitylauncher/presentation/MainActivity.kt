package com.teacher.productivitylauncher.presentation

import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.core.view.WindowCompat
import com.teacher.productivitylauncher.presentation.launcher.LauncherScreen
import com.teacher.productivitylauncher.presentation.theme.TeacherLauncherTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Make status bar and navigation bar transparent
        setupEdgeToEdge()

        setContent {
            TeacherLauncherTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    LauncherScreen()
                }
            }
            // Set status bar icons color based on theme
            SetStatusBarIconsColor()
        }
    }

    private fun setupEdgeToEdge() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            window.apply {
                clearFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS)
                addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                // Set status bar color to transparent
                statusBarColor = android.graphics.Color.TRANSPARENT

                // Make navigation bar transparent
                navigationBarColor = android.graphics.Color.TRANSPARENT
            }
        }
    }

    @Composable
    private fun SetStatusBarIconsColor() {
        val isDarkTheme = isSystemInDarkTheme()

        // Apply status bar icon colors
        val window = this.window
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            WindowCompat.getInsetsController(window, window.decorView).apply {
                // Light status bar icons for dark theme (and vice versa)
                isAppearanceLightStatusBars = !isDarkTheme
                // Light navigation bar icons for dark theme
                isAppearanceLightNavigationBars = !isDarkTheme
            }
        }
    }
}