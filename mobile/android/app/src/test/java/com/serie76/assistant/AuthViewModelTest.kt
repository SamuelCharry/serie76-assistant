package com.serie76.assistant

import androidx.lifecycle.ViewModel
import com.serie76.assistant.data.*
import com.serie76.assistant.ui.*
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.*
import org.junit.Assert.*
import retrofit2.HttpException
import retrofit2.Response

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    @Before fun setup() { Dispatchers.setMain(dispatcher) }
    @After fun teardown() { Dispatchers.resetMain() }
    private class Tokens(var value: String? = null) : TokenStore {
        override fun read() = value
        override fun write(token: String) { value = token }
        override fun clear() { value = null }
    }
    private class Api : AuthApi {
        var user = Account("a", "a@example.test", "Account A")
        var fail: Exception? = null
        var revoked = false
        var pendingMe: CompletableDeferred<Account>? = null
        override suspend fun login(request: LoginRequest): LoginResponse { fail?.let { throw it }; return LoginResponse(user.id + "-token", user) }
        override suspend fun me(): Account { pendingMe?.let { return it.await() }; fail?.let { throw it }; return user }
        override suspend fun logout() { fail?.let { throw it }; revoked = true }
    }
    private class SensitiveViewModel : ViewModel() {
        var cleared = false
        override fun onCleared() { cleared = true }
    }

    @Test fun `logout revokes token clears private viewmodels and next identity is fresh`() = runTest(dispatcher) {
        val api = Api(); val tokens = Tokens(); val vm = AuthViewModel(api, tokens, io = dispatcher)
        advanceUntilIdle(); assertNull(vm.state.value.user)
        vm.login("a@example.test", "synthetic password"); advanceUntilIdle()
        val firstGeneration = vm.state.value.generation
        val sensitive = SensitiveViewModel(); vm.chatOwner.viewModelStore.put("chat", sensitive)
        api.fail = java.io.IOException()
        vm.logout(); advanceUntilIdle()
        assertEquals("a", vm.state.value.user?.id); assertNotNull(tokens.value); assertFalse(sensitive.cleared)
        api.fail = null
        vm.logout(); advanceUntilIdle()
        assertTrue(api.revoked); assertNull(tokens.value); assertNull(vm.state.value.user); assertTrue(sensitive.cleared)
        api.user = Account("b", "b@example.test", "Account B")
        vm.login("b@example.test", "synthetic password"); advanceUntilIdle()
        assertEquals("b", vm.state.value.user?.id); assertNotEquals(firstGeneration, vm.state.value.generation)
        vm.expired("a-token"); advanceUntilIdle()
        assertEquals("b", vm.state.value.user?.id); assertEquals("b-token", tokens.value)
        vm.expired("b-token"); advanceUntilIdle()
        assertNull(vm.state.value.user); assertNull(tokens.value)
    }

    @Test fun `saved token must be verified before revealing conversations`() = runTest(dispatcher) {
        val api = Api(); val tokens = Tokens("saved-token")
        api.fail = java.io.IOException()
        val vm = AuthViewModel(api, tokens, io = dispatcher); advanceUntilIdle()
        assertNull(vm.state.value.user); assertNotNull(tokens.value); assertTrue(vm.state.value.canRetrySavedSession)
        api.fail = null; vm.restore(); advanceUntilIdle()
        assertEquals("a", vm.state.value.user?.id)
    }

    @Test fun `invalid saved session is removed and bad login never authenticates`() = runTest(dispatcher) {
        val api = Api(); val tokens = Tokens("saved-token")
        api.fail = HttpException(Response.error<Unit>(401, "{}".toResponseBody()))
        val vm = AuthViewModel(api, tokens, io = dispatcher); advanceUntilIdle()
        assertNull(tokens.value); assertNull(vm.state.value.user)
        vm.login("a@example.test", "incorrect"); advanceUntilIdle()
        assertNull(vm.state.value.user); assertFalse(vm.state.value.busy)
        assertEquals("Email or password is incorrect.", vm.state.value.error)
    }

    @Test fun `late restore failure cannot clear a newly authenticated identity`() = runTest(dispatcher) {
        val api = Api(); val tokens = Tokens("old-token")
        val pending = CompletableDeferred<Account>(); api.pendingMe = pending
        val vm = AuthViewModel(api, tokens, io = dispatcher); runCurrent()
        vm.expired("old-token"); runCurrent()
        api.user = Account("b", "b@example.test", "Account B")
        vm.login("b@example.test", "synthetic password"); runCurrent()
        assertEquals("b", vm.state.value.user?.id)
        pending.completeExceptionally(HttpException(Response.error<Unit>(401, "{}".toResponseBody())))
        advanceUntilIdle()
        assertEquals("b", vm.state.value.user?.id); assertEquals("b-token", tokens.value)
    }
}
