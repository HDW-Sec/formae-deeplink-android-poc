# syntax=docker/dockerfile:1
# Build de l'APK SANS Android Studio : juste un JDK, les command-line tools
# Android et Gradle. Le conteneur produit app-debug.apk, qu'on extrait ensuite.
#
# Le build doit cibler linux/amd64 (le flag est passé au `docker build`, voir
# build-apk.sh). Raison : l'outil aapt2 d'Android n'existe qu'en x86_64 et ne
# tourne pas sur arm64 (Mac Apple Silicon). En amd64, émulé par Docker/OrbStack,
# il fonctionne. Build un peu plus lent, mais portable.
FROM eclipse-temurin:17-jdk-jammy

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# --- Android command-line tools ---
ARG CMDLINE_TOOLS_VERSION=11076708
RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    curl -fsSL "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip" -o /tmp/cmdtools.zip && \
    unzip -q /tmp/cmdtools.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    rm /tmp/cmdtools.zip

ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools

# Licences + plateforme + build-tools
RUN yes | sdkmanager --licenses > /dev/null && \
    sdkmanager --install "platform-tools" "platforms;android-34" "build-tools;34.0.0" > /dev/null

# --- Gradle ---
ARG GRADLE_VERSION=8.5
RUN curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" -o /tmp/gradle.zip && \
    unzip -q /tmp/gradle.zip -d /opt && \
    rm /tmp/gradle.zip
ENV PATH=${PATH}:/opt/gradle-${GRADLE_VERSION}/bin

WORKDIR /project
COPY . /project

# Construit l'APK debug (signé avec la clé debug, donc installable directement).
# Le cache mount garde les dépendances Gradle entre les builds : on ne re-télécharge
# pas tout Maven à chaque changement de source (plus rapide et plus fiable).
RUN --mount=type=cache,target=/root/.gradle gradle --no-daemon assembleDebug

# Résultat : /project/app/build/outputs/apk/debug/app-debug.apk
