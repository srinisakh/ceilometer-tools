sudo apt-get -y update
sudo apt-get -y install git
sudo apt-get -y install git-review
sudo apt-get -y install vim
sudo apt-get -y install ansible
git clone http://github.com/srsakhamuri/ceilometer-tools
ansible-playbook -i "localhost," -c local ceilometer-tools/ansible-dev-playbook.yml
