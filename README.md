# Flask demo




# Deployment

Run ./install.sh. It will:

- create a virtual environment in this folder, called locutus.venv. This is where all the dependencies will be installed
- install the dependencies from app/requirements.txt. Note that now this file contains linux requirements; 
  conda interprets some system libraries as packages and will need them to be installed separately.
  See comments in the file for more details.
- install uwsgi. Most Python web applications expect HTTP requests in a certain format, WSGI. This is similar to CGI and FastCGI
  that were popular in the past, but works faster. Although flask contains a built-in HTTP server, it doesn't make use of threads
  and isn't considered secure; it is just a development server. In production, you offload this work to WSGI servers, which pack
  incoming socket data to understandable in-memory WSGI data strucures.
  `uwsgi` will create a unix socket `lockutus.sock` in this directory when active.
- create a service for uwsgi, so if/when it fails, system will restart the process automatically. Now you can start and stop the
  service with commands like `sudo service locutus start` or `sudo service locutus stop`.
- install nginx, if necessary. Most WSGI servers aren't good at handling network socket magic, like thousands of simultaneous,
  often slow, clients. So, on top of uwsgi server we set up a web server, which is good at it. As a bonus, nginx will also take
  care of serving static files, which it does a lot more efficiently than flask itself.

After this, the website should be operational
