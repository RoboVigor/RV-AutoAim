cd data
rm test?/ -rf
wget -O "data.zip" https://codeload.github.com/RoboVigor/RV-AutoAim-Data/zip/2.6.1
unzip data.zip
mv RV-AutoAim-Data-**/data/* .
rm RV-AutoAim-Data-* -rf
rm data.zip
