plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android' version '1.9.22'
}

android {
    namespace 'com.wynd.vpn'
    compileSdk 34

    defaultConfig {
        applicationId "com.wynd.vpn"
        minSdk 24
        targetSdk 34
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = '17'
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}