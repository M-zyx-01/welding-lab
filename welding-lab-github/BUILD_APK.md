# 焊接分析实验室 - 安卓APK构建指南
# Welding Intelligence Lab - Android APK Build Guide

## 方法一：在线PWA Builder（推荐，无需安装任何工具）
### Method 1: Online PWA Builder (Recommended, no tools needed)

1. 打开 https://www.pwabuilder.com/
2. 输入网站URL（部署后的地址）或者：
   - 如果你在本地运行，先用 ngrok 暴露端口: `ngrok http 8716`
   - 然后把 ngrok 提供的 https URL 粘贴到 PWA Builder
3. 点击 "Start" 按钮
4. 在 "Android" 卡片上点击 "Store Package"
5. 下载生成的 APK 文件
6. 传输到安卓手机安装

---

## 方法二：本地构建（需要JDK 17）
### Method 2: Local Build (requires JDK 17)

### 前提条件 / Prerequisites:
- JDK 17: https://adoptium.net/download/
- Android SDK Command-line Tools: https://developer.android.com/studio#command-line-tools-only

### 步骤 / Steps:
```bash
# 1. 安装依赖
npm install

# 2. 设置环境变量 (Windows)
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.13.11-hotspot
set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\Sdk

# 3. 安装Android SDK组件
sdkmanager "platforms;android-34" "build-tools;34.0.0" "platform-tools"

# 4. 同步并构建
npx cap sync android
cd android && gradlew.bat assembleDebug

# 5. APK位置 / APK location:
# android\app\build\outputs\apk\debug\app-debug.apk
```

或者直接运行一键脚本:
```bash
build_apk_easy.bat
```

---

## 方法三：使用Android Studio
### Method 3: Using Android Studio

1. 安装 Android Studio: https://developer.android.com/studio
2. 打开本项目的 `android` 文件夹
3. Android Studio 会自动配置 SDK 和依赖
4. Build > Build Bundle(s) / APK(s) > Build APK(s)

---

## 当前PWA状态 / Current PWA Status:
- ✅ manifest.json - 已配置
- ✅ Service Worker - 已配置（离线缓存）
- ✅ 应用图标 - 已生成（72x72 ~ 512x512）
- ✅ 响应式设计 - 移动端适配
- ✅ Capacitor Android 项目 - 已初始化

## PWA直接安装（安卓手机）
### Install PWA directly on Android:
1. 在安卓手机上用 Chrome 打开网站
2. 点击右上角菜单 (⋮)
3. 选择 "添加到主屏幕" / "Add to Home Screen"
4. 将以全屏App形式出现在主屏幕
