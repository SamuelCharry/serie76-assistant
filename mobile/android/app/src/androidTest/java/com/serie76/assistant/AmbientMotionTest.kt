package com.serie76.assistant

import android.os.ParcelFileDescriptor
import androidx.compose.runtime.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.test.platform.app.InstrumentationRegistry
import com.serie76.assistant.ui.ambientClock
import com.serie76.assistant.ui.rememberAmbientPhase
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class AmbientMotionTest {
    @get:Rule val compose = createComposeRule()

    @Test fun ambientClockPausesWhenHiddenAndBelowResumed() {
        val owner = object : LifecycleOwner {
            val registry = LifecycleRegistry(this)
            override val lifecycle: Lifecycle get() = registry
        }
        val visible = mutableStateOf(true)
        lateinit var phase: State<Float>
        compose.runOnUiThread { owner.registry.currentState = Lifecycle.State.RESUMED }
        compose.setContent { CompositionLocalProvider(LocalLifecycleOwner provides owner) { phase = ambientClock(visible.value) } }
        compose.waitUntil(3000) { phase.value > 0f }
        compose.runOnIdle { visible.value = false }
        compose.waitForIdle()
        val hidden = phase.value
        Thread.sleep(250)
        assertEquals(hidden, phase.value, 0f)
        compose.runOnIdle { visible.value = true }
        compose.waitUntil(3000) { phase.value > hidden }
        compose.runOnUiThread { owner.registry.currentState = Lifecycle.State.STARTED }
        compose.waitForIdle()
        val paused = phase.value
        Thread.sleep(250)
        assertEquals(paused, phase.value, 0f)
        compose.runOnUiThread { owner.registry.currentState = Lifecycle.State.RESUMED }
        compose.waitUntil(3000) { phase.value > paused }
    }

    @Test fun androidRemoveAnimationsStopsMountedBackground() {
        val original = shell("settings get global animator_duration_scale").trim()
        lateinit var phase: State<Float>
        try {
            shell("settings put global animator_duration_scale 1")
            compose.setContent { phase = rememberAmbientPhase(true) }
            compose.waitUntil(3000) { phase.value > 0f }
            shell("settings put global animator_duration_scale 0")
            // ContentObserver delivery is asynchronous; wait past its dispatch before sampling.
            Thread.sleep(300)
            compose.waitForIdle()
            val stopped = phase.value
            Thread.sleep(250)
            assertEquals(stopped, phase.value, 0f)
            shell("settings put global animator_duration_scale 1")
            compose.waitUntil(3000) { phase.value > stopped }
        } finally {
            if (original == "null") shell("settings delete global animator_duration_scale")
            else shell("settings put global animator_duration_scale $original")
        }
    }

    private fun shell(command: String): String = ParcelFileDescriptor.AutoCloseInputStream(
        InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommand(command)
    ).bufferedReader().use { it.readText() }
}
