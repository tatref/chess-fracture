#!/bin/bash
# Works on AWS RHEL 7.4 x86_64 image

set -eux

VNC_DISPLAY=1


rpm -q epel-release || sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
#sudo yum groupinstall -y "Server with GUI"



sudo yum install -y yum-utils zip xorg-x11-server-Xorg xorg-x11-xauth xorg-x11-server-utils mesa-dri-drivers
sudo yum-config-manager --enable rhui-REGION-rhel-server-extras
sudo yum install -y docker docker-compose
sudo groupadd docker || true
sudo usermod -a -G docker ec2-user
cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "live-restore": true,
  "group": "docker"
}
EOF

sudo systemctl enable docker
sudo systemctl start docker

sudo curl -L https://github.com/docker/compose/releases/download/1.20.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo curl -L https://raw.githubusercontent.com/docker/compose/1.20.1/contrib/completion/bash/docker-compose -o /etc/bash_completion.d/docker-compose



# turbovnc 2.2 (dev) allows gl under vnc
rpm -q turbovnc || sudo yum install -y turbovnc-2.1.80.x86_64.rpm

cat <<EOF | sudo tee /etc/sysconfig/tvncservers
VNCSERVERS="$VNC_DISPLAY:ec2-user"
VNCSERVERARGS[1]="-geometry 800x600 -nohttpd -localhost"
EOF

mkdir -p /home/ec2-user/.vnc
echo ec2-user | /opt/TurboVNC/bin/vncpasswd -f | sudo -Eu ec2-user tee /home/ec2-user/.vnc/passwd

sudo -Eu ec2-user /opt/TurboVNC/bin/vncserver :1

sudo systemctl enable tvncserver.service
sudo systemctl start tvncserver.service



