plugins {
    id("com.android.application")
}

android {
    namespace = "com.gabrc.marcadorasistencia"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.gabrc.marcadorasistencia"
        minSdk = 27
        targetSdk = 37
        versionCode = 2
        versionName = "1.1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    testOptions {
        unitTests.isIncludeAndroidResources = true
        unitTests.all { it.systemProperty("capturas", findProperty("capturas") ?: "") }
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.1")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("com.google.android.material:material:1.14.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.16.1")
    testImplementation("androidx.test:core:1.7.0")
}
