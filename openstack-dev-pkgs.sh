sudo apt-get update
sudo apt-get install git
sudo apt-get install ansible
git clone http://github.com/srsakhamuri/ceilometer-tools
ansible-playbook -i "localhost," -c local ansible-dev-playbook.yml
