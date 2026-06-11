package com.hdwsec.formaepoc

import java.net.HttpURLConnection
import java.net.URL

/**
 * La couche réseau de l'application.
 *
 * LE DÉFAUT CENTRAL : on attache le jeton d'authentification à TOUTES les
 * requêtes sortantes, sans jamais regarder vers quel domaine elles partent.
 * Combiné au routeur vulnérable, ça suffit à exfiltrer le jeton.
 */
object ApiClient {

    fun download(url: String, accessToken: String): String {
        // --- Correctif (volontairement désactivé pour la démo) ---------------
        // N'attacher le jeton que si l'hôte est de confiance :
        //
        //   if (!URL(url).host.endsWith(".formae.com")) {
        //       // domaine non fiable -> on n'envoie PAS le jeton
        //   }
        // ---------------------------------------------------------------------
        return try {
            val conn = (URL(url).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                // Le jeton, attaché aveuglément à la requête :
                setRequestProperty("Authorization", "Bearer $accessToken")
                setRequestProperty("User-Agent", "FormaeApp/1.0 (PoC)")
                connectTimeout = 5000
                readTimeout = 5000
            }
            val code = conn.responseCode
            conn.disconnect()
            "HTTP $code"
        } catch (e: Exception) {
            "Erreur réseau : ${e.message}"
        }
    }
}
