FROM python:3.11
WORKDIR /usr/src/app

# Install pyfiche from the git repository
RUN pip install -U git+https://kumig.it/PrivateCoffee/pyfiche.git

# Install supervisord
RUN pip install supervisor

# Create a directory where pyfiche will store its data
RUN mkdir data

# Copy the supervisord configuration file into the container
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the ports that pyfiche, recup, and lines will run on
EXPOSE 9999
EXPOSE 9998
EXPOSE 9997

# Use VOLUME to allow data persistence
VOLUME ["/usr/src/app/data"]

# Run supervisord to manage the services
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
