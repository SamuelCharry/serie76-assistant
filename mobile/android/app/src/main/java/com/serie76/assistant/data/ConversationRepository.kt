package com.serie76.assistant.data

import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.io.IOException
import java.io.InterruptedIOException
import java.net.ConnectException
import java.net.UnknownHostException
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.contentOrNull
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.ConnectionPool
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.DELETE
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

val wireJson = Json { ignoreUnknownKeys = true; explicitNulls = false }

interface ConversationRepository {
    suspend fun sessions(offset: Int = 0): SessionsPage
    suspend fun messages(sessionId: String, before: Long? = null): MessagesPage
    suspend fun send(query: String, sessionId: String?, answers: Map<String, String> = emptyMap(),
                     removeFilters: List<String> = emptyList(), action: SuggestionAction? = null): ConversationResponse
    suspend fun deleteSession(sessionId: String)
}

interface ConversationApi {
    @GET("api/sessions") suspend fun sessions(@Query("offset") offset: Int): SessionsPage
    @GET("api/sessions/{id}/messages")
    suspend fun messages(@Path("id") id: String, @Query("before") before: Long?): MessagesPage
    @POST("api/conversation") suspend fun conversation(@Body request: ConversationRequest): ConversationResponse
    @DELETE("api/sessions/{id}") suspend fun deleteSession(@Path("id") id: String): retrofit2.Response<Unit>
}

class ApiConversationRepository(private val api: ConversationApi) : ConversationRepository {
    override suspend fun sessions(offset: Int) = api.sessions(offset)
    override suspend fun messages(sessionId: String, before: Long?) = api.messages(sessionId, before)
    override suspend fun send(query: String, sessionId: String?, answers: Map<String, String>, removeFilters: List<String>, action: SuggestionAction?) =
        api.conversation(ConversationRequest(query, sessionId, answers, removeFilters, action))
    override suspend fun deleteSession(sessionId: String) {
        val response = api.deleteSession(sessionId)
        if (!response.isSuccessful) throw HttpException(response)
    }
}

// The backend has a 60 s agent deadline; allow time for connection and the final error response.
internal fun conversationHttpClient(bearer: () -> String? = { null }, expired: (String) -> Unit = {}): OkHttpClient =
    OkHttpClient.Builder()
        .connectionPool(ConnectionPool(5, 30, TimeUnit.SECONDS))
        .followRedirects(false)
        .followSslRedirects(false)
        .addInterceptor { chain ->
            val token = bearer()
            val request = chain.request().newBuilder().apply { token?.let { header("Authorization", "Bearer $it") } }.build()
            chain.proceed(request).also { response ->
                if (response.code == 401 && token != null && request.url.encodedPath != "/api/auth/login") expired(token)
            }
        }
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(70, TimeUnit.SECONDS)
        .callTimeout(75, TimeUnit.SECONDS)
        .retryOnConnectionFailure(false)
        .build()

fun createRetrofit(url: String, bearer: () -> String? = { null }, expired: (String) -> Unit = {}): Retrofit = Retrofit.Builder()
    .baseUrl(url)
    .client(conversationHttpClient(bearer, expired))
    .addConverterFactory(wireJson.asConverterFactory("application/json".toMediaType()))
    .build()

private fun errorCode(error: HttpException): String? = runCatching {
    // Reading a copy keeps classification and message rendering independent.
    val source = error.response()?.errorBody()?.source() ?: return@runCatching null
    source.request(Long.MAX_VALUE)
    wireJson.parseToJsonElement(source.buffer.clone().readUtf8()).jsonObject["error_code"]?.jsonPrimitive?.contentOrNull
}.getOrNull()

fun requiresReconciliation(error: Throwable): Boolean = when (error) {
    is UnknownHostException, is ConnectException -> false
    is HttpException -> error.code() == 409 || (error.code() >= 500 && errorCode(error) != "not_configured")
    else -> true // A lost or invalid response does not prove the server failed to save the turn.
}

fun failureMessage(error: Throwable): String = when (error) {
    is HttpException -> when (error.code()) {
        401 -> "Your session has expired. Please sign in again."
        402 -> "The assistant's service budget has run out. Please contact the administrator and try again later."
        404 -> "This conversation could not be found. Return to Conversations and refresh."
        409 -> "A response is already being prepared. Reload the conversation before sending again."
        422 -> "The request could not be accepted. Check your message and try again."
        429 -> "Too many requests. Please wait before trying again."
        503 -> {
            val code = errorCode(error)
            when (code) {
                "not_configured" -> "The assistant is not configured on the server."
                "database_unavailable" -> "Saved conversations are temporarily unavailable. Please try again shortly."
                else -> "The assistant is temporarily unavailable. Please try again."
            }
        }
        500 -> "The server could not complete the request. Please try again shortly."
        502 -> "The assistant's service could not respond. Please try again shortly."
        504 -> "The assistant's service took too long to respond. Please try again shortly."
        else -> "The assistant is unavailable. Check that the backend is running and configured."
    }
    is InterruptedIOException -> "The server took too long to respond. Please try again shortly."
    is IOException -> "Cannot reach the backend. Check your connection and the backend address."
    else -> "The response could not be loaded. Please try again."
}

fun emptyCombinationMessage(error: Throwable): String? {
    if (error !is HttpException || error.code() != 422) return null
    return runCatching {
        val body = error.response()?.errorBody()?.string() ?: return@runCatching null
        val parsed = wireJson.parseToJsonElement(body).jsonObject
        if (parsed["error_code"]?.jsonPrimitive?.contentOrNull == "empty_combination")
            parsed["detail"]?.jsonPrimitive?.contentOrNull else null
    }.getOrNull()
}
