package com.serie76.assistant.data

import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

val wireJson = Json { ignoreUnknownKeys = true; explicitNulls = false }

interface ConversationRepository {
    suspend fun sessions(offset: Int = 0): SessionsPage
    suspend fun messages(sessionId: String, before: Long? = null): MessagesPage
    suspend fun send(query: String, sessionId: String?): ConversationResponse
}

interface ConversationApi {
    @GET("api/sessions") suspend fun sessions(@Query("offset") offset: Int): SessionsPage
    @GET("api/sessions/{id}/messages")
    suspend fun messages(@Path("id") id: String, @Query("before") before: Long?): MessagesPage
    @POST("api/conversation") suspend fun conversation(@Body request: ConversationRequest): ConversationResponse
}

class ApiConversationRepository(private val api: ConversationApi) : ConversationRepository {
    override suspend fun sessions(offset: Int) = api.sessions(offset)
    override suspend fun messages(sessionId: String, before: Long?) = api.messages(sessionId, before)
    override suspend fun send(query: String, sessionId: String?) = api.conversation(ConversationRequest(query, sessionId))
}

fun createRetrofit(url: String, bearer: () -> String? = { null }, expired: (String) -> Unit = {}): Retrofit = Retrofit.Builder()
    .baseUrl(url)
    .client(OkHttpClient.Builder()
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
        .build())
    .addConverterFactory(wireJson.asConverterFactory("application/json".toMediaType()))
    .build()

fun failureMessage(error: Throwable): String = when (error) {
    is HttpException -> when (error.code()) {
        401 -> "Your session has expired. Please sign in again."
        404 -> "This conversation could not be found. Return to Conversations and refresh."
        409 -> "A response is already being prepared. Reload the conversation before sending again."
        422 -> "The request could not be accepted. Check your message and try again."
        429 -> "Too many requests. Please wait before trying again."
        else -> "The assistant is unavailable. Check that the backend is running and configured."
    }
    is IOException -> "Cannot reach the backend. Check your connection and the backend address."
    else -> "The response could not be loaded. Please try again."
}
