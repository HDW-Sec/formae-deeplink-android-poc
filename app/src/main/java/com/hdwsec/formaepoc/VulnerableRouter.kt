package com.hdwsec.formaepoc

import android.net.Uri

/**
 * La logique de routage des deep links. Dans la vraie application, elle est
 * partagée entre Android et iOS (un seul code, deux plateformes touchées).
 * C'est ici que vivent les deux défauts qu'on enchaîne.
 */
object VulnerableRouter {

    /**
     * Étape 1 — redirection ouverte.
     * La route /api/track/click sert à tracer les clics dans les emails. Elle
     * renvoie le paramètre `url` tel quel comme nouvelle cible, SANS vérifier
     * le domaine de destination. N'importe quelle URL externe passe donc.
     */
    fun resolveOpenRedirect(link: Uri): Uri? {
        if (link.path != "/api/track/click") return null
        val url = link.getQueryParameter("url") ?: return null
        return Uri.parse(url)
    }

    /**
     * Étape 2 — route de téléchargement du certificat.
     * Elle reconstruit l'URL de l'API interne (/api/documents/certificate/{id})
     * mais en RECYCLANT le domaine de l'URL d'entrée, sans le valider. Comme ce
     * domaine est désormais celui de l'attaquant, la requête part chez lui.
     */
    fun resolveCertificateDownload(target: Uri): String? {
        val id = Regex("^/downloads/certificate/([^/]+)$")
            .find(target.path.orEmpty())?.groupValues?.get(1) ?: return null
        val host = target.host ?: return null
        val scheme = target.scheme ?: "https"
        val port = if (target.port != -1) ":${target.port}" else ""
        return "$scheme://$host$port/api/documents/certificate/$id"
    }
}
