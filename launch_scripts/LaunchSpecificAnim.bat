@echo off
echo Please type the desired file id down below:

set /p anim=""

echo Playing %anim%

start .\..\aRGBeX.exe --play_id %anim%
start .\..\aRGBeX-Simulator.exe
