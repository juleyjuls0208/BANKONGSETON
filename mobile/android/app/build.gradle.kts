plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.juls.bankongsetonandroid"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.juls.bankongsetonandroid"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.constraintlayout)
    
    // CardView for material cards
    implementation("androidx.cardview:cardview:1.0.0")
    
    // RecyclerView for lists
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    
    // SwipeRefreshLayout for pull-to-refresh
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
    
    // Retrofit for API calls
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    
    // OkHttp for network calls
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.11.0")
    
    // Gson for JSON parsing
    implementation("com.google.code.gson:gson:2.10.1")
    
    // Biometric authentication for NFC payments
    implementation("androidx.biometric:biometric:1.1.0")
    
    // Security for encrypted storage
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}