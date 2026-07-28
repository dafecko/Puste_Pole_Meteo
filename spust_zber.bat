@echo off
cd /d "C:\Users\DFecko\Desktop\Puste_Pole_Meteo"

echo 1. Spustam aktualizaciu pocasia...
python update_weather.py
python meteo_zber_v2.py

echo 2. Pridavam zmeny CSV suborov do Gitu...
git add meteo_aktualne.csv meteo_puste_pole_v2.csv

echo 3. Vytvaram commit...
git commit -m "Automaticka aktualizacia meteo dat"

echo 4. Posielam na GitHub...
git push origin main

echo Vsetko prebehlo uspesne!
pause