pyinstaller src/main.spec
pyinstaller src/simulator.spec

move .\dist\aRGBeX.exe .\aRGBeX.exe
move .\dist\aRGBeX-Simulator.exe .\aRGBeX-Simulator.exe

pause