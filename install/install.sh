hostnamectl set-hostname args[1]

# opentestbed
apt-get update
apt-get install -y gcc-arm-none-eabi
pip install intelhex
pip install paho-mqtt
pip install supervisor

git clone -b develop https://github.com/openwsn-berkeley/opentestbed.git

cp /opentestbed/intall/supervisord.conf /etc/
mkdir /home/opentestbed/latest
cp /opentestbed/intall/otswtoload.json /home/opentestbed/latest/
cp /opentestbed/intall/otbootload.py /home/opentestbed/

rm -r opentestbed/

# To show images
apt-get install feh

# install display
rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
./LCD35-show
