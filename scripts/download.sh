cd data
rm test?/ -rf
wget -O "data.zip" https://github.com/RoboVigor/RV-AutoAim-Data/archive/3.1.zip
unzip data.zip
mv RV-AutoAim-Data-**/data/* .
rm RV-AutoAim-Data-* -rf
rm data.zip
