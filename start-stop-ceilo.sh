sudo service ceilometer-collector $1
sudo service ceilometer-agent-notification $1
sudo service ceilometer-alarm-notifier $1
sudo service ceilometer-agent-compute $1
sudo service ceilometer-alarm-evaluator $1
sudo service ceilometer-agent-central $1
sudo service ceilometer-api $1
# If using apaceh2 on Helion
a2ensite ceilometer_modwsgi.conf
service apache2 reload
