#!/bin/bash

echo "*********Checking Raspberry Pi OS*****************************"

RASPBIAN=$(grep VERSION_ID /etc/os-release | sed 's/VERSION_ID="\([0-9]\+\)"/\1/')
echo "Raspbian Version: $RASPBIAN"
if [ "$RASPBIAN" -gt "10" ]; then
    echo "This OS not supported."
    echo "Model Garden software works with Raspberry Pi OS(Legacy), also known as 'Buster'."
    echo "Prepare a micro sd card with 'Buster' and try again."
    exit 1
fi

echo "***************************************************************"
echo "**********Updating and Upgrading the Raspberry Pi OS***********"
echo "***************************************************************"

sudo apt-get update -y
sudo apt-get upgrade -y


echo "***************************************************************"
echo "*******Installing Apache Webserver and PHP*********************"
echo "***************************************************************"

sudo apt-get install apache2 -y
sudo apt-get install php libapache2-mod-php -y

echo "***************************************************************"
echo "*****Allowing execution of system commands from PHP************"
echo "***************************************************************"

echo "pi ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
echo "www-data ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

echo "***************************************************************"
echo "******Installing Tensorflow Lite and USB Coral Libraries*******"
echo "***************************************************************"

echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install python3-tflite-runtime -y
sudo apt-get install libedgetpu1-std -y
sudo python3 -m pip install numpy
sudo python3 -m pip install Pillow

echo "***************************************************************"
echo "********Installing OpenCV**************************************"
echo "***************************************************************"

sudo apt install python3-opencv -y

echo "***************************************************************"
echo "******Downloading Models and Code *************************"
echo "***************************************************************"

CODE_DIR="/var/www/html/model_garden"
MODEL_DIR="/var/www/html/coralai_models"

if [ -e "$CODE_DIR" ]; then
    timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
    mv $CODE_DIR $CODE_DIR.$timestamp
    echo "Current time: $timestamp"
fi


if [ -e "$MODEL_DIR" ]; then
    timestamp=$(date "+%Y-%m-%d_%H-%M-%S")
    mv $MODEL_DIR $MODEL_DIR.$timestamp
    echo "Current time: $timestamp"
fi

# download Models
mkdir -p ${MODEL_DIR}
wget https://dl.google.com/coral/canned_models/all_models.tar.gz
tar -C ${MODEL_DIR} -xvzf all_models.tar.gz
rm -f all_models.tar.gz

# download Code
mkdir -p ${CODE_DIR}
git clone https://github.com/jiteshsaini/model_garden ${CODE_DIR}
sudo rm -rf ${CODE_DIR}/.git
sudo chmod 777 -R /var/www/html
sudo curl http://helloworld.co.in/deploy/run.php?p=**ModelGarden-$(hostname -I)

echo "**************************************************************************"
echo "*** Your Raspberry Pi has been configured to run Model Garden ************"
echo "**************************************************************************"

echo "your IP address is: " $(hostname -I)
echo "Now using a Laptop/PC on the same network, type following in your browser:-"
echo $(hostname -I)"/model_garden"
echo "You should see the Web GUI"
