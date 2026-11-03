package com.serie76.assistant

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.SystemBarStyle
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.runtime.*
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
        )
        val appContext = applicationContext
        val authFactory = viewModelFactory { initializer {
            val tokens = SecureTokenStore(appContext)
            lateinit var holder: AuthViewModel
            val client = createRetrofit(BuildConfig.BACKEND_URL, tokens::read) { token -> holder.expired(token) }
            holder = AuthViewModel(client.create(AuthApi::class.java), tokens, client)
            holder
        } }
        setContent { SeriesTheme {
            val auth: AuthViewModel = viewModel(factory = authFactory)
            val retrofit = requireNotNull(auth.authenticatedApi)
            val state by auth.state.collectAsStateWithLifecycle()
            val user = state.user
            if (user == null) LoginScreen(state, auth::login, auth::restore)
            else key(state.generation) {
                val factory = remember { viewModelFactory { initializer {
                    AppViewModel(ApiConversationRepository(retrofit.create(ConversationApi::class.java)), SavedStateHandle())
                } } }
                CompositionLocalProvider(LocalAccount provides AccountControls(user, state.busy, state.error, auth::logout),
                    LocalAuthenticatedApi provides retrofit) {
                    SeriesApp(viewModel(viewModelStoreOwner = auth.chatOwner, factory = factory))
                }
            }
        } }
    }
}
