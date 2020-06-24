#!/bin/bash
# need to do this to get dependencies
sudo apt-get install python3-venv

PROJECT_NAME=locutus
CURRENT_DIR=`pwd`
DEPLOY_DIR=/var/www/locutus
VENV_DIR=${PROJECT_NAME}.venv

mkdir ${VENV_DIR}
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate
pip install -r app/requirements.txt

# install uwsgi and create systemd service
pip install uwsgi

sudo ln -s ${CURRENT_DIR} ${DEPLOY_DIR}

echo """
[Unit]
Description=uWSGI instance to serve Bogdan's pet project
After=network.target

[Service]
User=bogdan
Group=www-data
WorkingDirectory=${DEPLOY_DIR}
Environment="PATH=${DEPLOY_DIR}/${VENV_DIR}/bin"
ExecStart=${DEPLOY_DIR}/${VENV_DIR}/bin/uwsgi --ini uwsgi.ini

[Install]
WantedBy=multi-user.target
""" > ${PROJECT_NAME}.service

sudo mv ${PROJECT_NAME}.service /etc/systemd/system/

sudo systemctl start ${PROJECT_NAME}


# Nginx part
sudo apt-get install nginx
echo """
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        # TODO: set up letsencrypt certificates autogen

        server_name _;

        location /static/ {
            root /var/www/locutus/app/;
        }

        location / { try_files $uri @locutus; }
        location @locutus {
            include uwsgi_params;
            uwsgi_pass unix:/var/www/locutus/locutus.sock;
        }

}
""" > ${PROJECT_NAME}.nginx

sudo mv ${PROJECT_NAME}.nginx /etc/nginx/sites-available/${PROJECT_NAME}
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/${PROJECT_NAME} /etc/nginx/sites-enabled/${PROJECT_NAME}
sudo service nginx restart
