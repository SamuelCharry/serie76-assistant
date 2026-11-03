package com.serie76.assistant.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelStore
import androidx.lifecycle.ViewModelStoreOwner
import androidx.lifecycle.viewModelScope
import com.serie76.assistant.data.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import retrofit2.Retrofit
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.UUID

data class AuthState(val user: Account? = null, val checking: Boolean = true, val busy: Boolean = false,
                     val error: String? = null, val generation: String = UUID.randomUUID().toString(),
                     val canRetrySavedSession: Boolean = false)

class AuthViewModel(private val api: AuthApi, private val tokens: TokenStore, val authenticatedApi: Retrofit? = null,
                    private val io: CoroutineDispatcher = Dispatchers.IO) : ViewModel() {
    private val tokenMutex = Mutex()
    private var operation = 0
    private val mutable = MutableStateFlow(AuthState())
    val state = mutable.asStateFlow()
    val chatOwner = object : ViewModelStoreOwner { override val viewModelStore = ViewModelStore() }
    init { restore() }

    fun restore() {
        val attempt = ++operation
        viewModelScope.launch {
            mutable.value = mutable.value.copy(checking = true, error = null)
            try {
                val token = withContext(io) { tokens.read() }
                val restored = if (token == null) null else api.me()
                if (attempt == operation) mutable.value = AuthState(user = restored, checking = false)
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) {
                tokenMutex.withLock {
                    if (attempt == operation) {
                        if (error is HttpException && error.code() == 401) withContext(io) { tokens.clear() }
                        if (attempt == operation) mutable.value = AuthState(checking = false,
                            canRetrySavedSession = !(error is HttpException && error.code() == 401), error = if (error is HttpException && error.code() == 401)
                                "Your session has expired. Please sign in again." else "Cannot verify your session. Check your connection and retry.")
                    }
                }
            }
        }
    }

    fun login(email: String, password: String) {
        if (mutable.value.busy) return
        val attempt = ++operation
        mutable.value = mutable.value.copy(busy = true, error = null, canRetrySavedSession = false)
        viewModelScope.launch {
            try {
                val response = api.login(LoginRequest(email.trim(), password))
                tokenMutex.withLock {
                    if (attempt != operation) return@withLock
                    withContext(io) { tokens.write(response.access_token) }
                    chatOwner.viewModelStore.clear()
                    mutable.value = AuthState(user = response.user, checking = false)
                }
            } catch (error: CancellationException) { throw error }
            catch (error: Exception) {
                if (attempt == operation) mutable.value = mutable.value.copy(busy = false, error = when {
                    error is HttpException && error.code() == 401 -> "Email or password is incorrect."
                    error is HttpException && error.code() == 429 -> "Too many attempts. Please wait before trying again."
                    else -> "Cannot sign in. Check your connection and try again."
                })
            }
        }
    }

    fun logout() {
        if (mutable.value.busy) return
        val generation = mutable.value.generation
        mutable.value = mutable.value.copy(busy = true, error = null)
        viewModelScope.launch {
            try {
                try { api.logout() } catch (error: HttpException) { if (error.code() != 401) throw error }
                tokenMutex.withLock {
                    if (mutable.value.generation == generation) {
                        withContext(io) { tokens.clear() }
                        chatOwner.viewModelStore.clear()
                        mutable.value = AuthState(checking = false)
                    }
                }
            } catch (error: CancellationException) { throw error }
            catch (_: Exception) {
                if (mutable.value.generation == generation) mutable.value = mutable.value.copy(busy = false, error = "Could not sign out. Reconnect and try again.")
            }
        }
    }

    /** Only an unauthorized response for the current bearer may expire this identity. */
    fun expired(token: String) {
        viewModelScope.launch {
            tokenMutex.withLock {
                if (withContext(io) { tokens.read() } == token) {
                    withContext(io) { tokens.clear() }
                    chatOwner.viewModelStore.clear()
                    if (!(mutable.value.busy && mutable.value.user == null)) {
                        mutable.value = AuthState(checking = false, error = "Your session has expired. Please sign in again.")
                    }
                }
            }
        }
    }

    override fun onCleared() { chatOwner.viewModelStore.clear() }
}
