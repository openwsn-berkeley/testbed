hostnamectl set-hostname $1

# opentestbed
apt-get update
apt-get install -y gcc-arm-none-eabi
pip install -r requirements.txt
apt-get install python-imaging-tk

git clone -b develop https://github.com/openwsn-berkeley/opentestbed.git

cp opentestbed/install/supervisord.conf /etc/
mkdir /home/opentestbed
mkdir /home/opentestbed/latest
cp opentestbed/install/otswtoload.json /home/opentestbed/latest/
cp opentestbed/install/otbootload.py /home/opentestbed/

rm -r opentestbed/

# change crontab

echo "@reboot sudo supervisord" >> crontabfile.txt
crontab crontabfile.txt


# install display
rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
./LCD35-show

# add udev rule for openmote-b 
cp 99-openmote-b.rules /etc/udev/rules.d/

# the rpi will reboot
