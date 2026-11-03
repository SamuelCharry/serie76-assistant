package com.serie76.assistant

import com.serie76.assistant.ui.AppearanceMode
import org.junit.Assert.assertEquals
import org.junit.Test

class AppearanceTest {
    @Test fun previousBinaryChoiceIsPreservedUntilANewModeIsSelected() {
        assertEquals(AppearanceMode.Dark, AppearanceMode.restored(null, true))
        assertEquals(AppearanceMode.Light, AppearanceMode.restored(null, false))
        assertEquals(AppearanceMode.System, AppearanceMode.restored(null, null))
    }

    @Test fun explicitSystemOverridesThePreviousManualChoice() {
        assertEquals(AppearanceMode.System, AppearanceMode.restored("system", true))
        assertEquals(AppearanceMode.Light, AppearanceMode.restored("light", true))
        assertEquals(AppearanceMode.Dark, AppearanceMode.restored("dark", false))
        assertEquals(AppearanceMode.System, AppearanceMode.restored("unknown", true))
    }
}
