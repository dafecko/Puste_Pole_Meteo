@echo off
cd /d "C:\Users\DFecko\Desktop\Puste_Pole_Meteo"

echo 1. Spustam aktualizaciu pocasia...
python update_weather.py
python meteo_zber_v2.py

echo 2. Stahujem pripadne zmeny z GitHubu...
git pull origin main --rebase

echo 3. Pridavam zmeny CSV suborov do Gitu...
git add meteo_aktualne.csv meteo_puste_pole_v2.csv

echo 4. Vytvaram commit...
git commit -m "Automaticka aktualizacia meteo dat"

echo 5. Posielam na GitHub...
git push origin main

echo Vsetko prebehlo uspesne!
pause