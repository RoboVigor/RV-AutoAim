cd data
rm test?/ -rf
wget https://codeload.github.com/RoboVigor/RV-AutoAim-Data/zip/2.6.1
unzip RV-AutoAim-Data-2.6.1.zip
mv RV-AutoAim-Data-2.6.1/data/* .
rm RV-AutoAim-Data-2.6.1 -rf
rm RV-AutoAim-Data-2.6.1.zip