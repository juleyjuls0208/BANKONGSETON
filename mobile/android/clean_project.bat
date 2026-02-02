@echo off
echo Cleaning Android project...
echo.

cd /d "L:\Louis\Desktop\BANKONGSETON\ANDROID"

echo Deleting .gradle folder...
if exist ".gradle" rmdir /s /q ".gradle"

echo Deleting .idea folder...
if exist ".idea" rmdir /s /q ".idea"

echo Deleting app\build folder...
if exist "app\build" rmdir /s /q "app\build"

echo Deleting build folder...
if exist "build" rmdir /s /q "build"

echo.
echo ✓ Clean complete!
echo.
echo Now:
echo 1. Open Android Studio
echo 2. Open this project: L:\Louis\Desktop\BANKONGSETON\ANDROID
echo 3. Wait for Gradle sync
echo.
pause
