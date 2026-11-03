package com.serie76.assistant.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import kotlinx.serialization.Serializable
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

@Serializable data class Account(val id: String, val email: String, val name: String)
@Serializable data class LoginRequest(val email: String, val password: String)
@Serializable data class LoginResponse(val access_token: String, val user: Account)

interface AuthApi {
    @POST("api/auth/login") suspend fun login(@Body request: LoginRequest): LoginResponse
    @GET("api/auth/me") suspend fun me(): Account
    @POST("api/auth/logout") suspend fun logout()
}

interface TokenStore {
    fun read(): String?
    fun write(token: String)
    fun clear()
}

/** The bearer is encrypted with a non-exportable Android Keystore AES-GCM key. */
class SecureTokenStore(context: Context) : TokenStore {
    private val preferences = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
    private val alias = "series76.auth.v1"
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        return (store.getKey(alias, null) as? SecretKey) ?: KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
            generateKey()
        }
    }
    @Synchronized override fun read(): String? {
        val saved = preferences.getString("bearer", null) ?: return null
        return try {
            val parts = saved.split(':')
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)))
            String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8)
        } catch (_: Exception) { clear(); null }
    }
    @Synchronized override fun write(token: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val value = Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" + Base64.encodeToString(cipher.doFinal(token.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
        check(preferences.edit().putString("bearer", value).commit()) { "Could not save session" }
    }
    @Synchronized override fun clear() { check(preferences.edit().clear().commit()) { "Could not remove session" } }
}
