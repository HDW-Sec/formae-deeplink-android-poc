plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.hdwsec.formaepoc"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.hdwsec.formaepoc"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        getByName("debug") {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

// Aucune dépendance externe : on reste sur l'Activity de base et HttpURLConnection,
// pour un build léger et reproductible (pas d'AndroidX, pas de Compose).
