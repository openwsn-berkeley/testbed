
# opentestbed
apt-get update
apt-get install -y gcc-arm-none-eabi
pip install intelhex
pip install paho-mqtt
pip install supervisor


cp supervisord.conf /etc/
mkdir latest
cp otswtoload.json latest/


# To show images
apt-get install feh

# install display
rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
./LCD35-show
