cd data
rm test?/ -rf
wget https://github.com/RoboVigor/RV-AutoAim-Data/archive/2.4.1.zip
unzip 2.4.1.zip
mv RV-AutoAim-Data-2.4.1/data/* .
rm RV-AutoAim-Data-2.4.1 -rf
rm 2.4.1.zip