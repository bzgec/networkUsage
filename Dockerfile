####################################################################################################
# pull official base image
####################################################################################################
FROM python:3.9-slim-buster

####################################################################################################
# set environment variables
####################################################################################################
# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1

# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

ENV HOME=/home/networkUsage

####################################################################################################
# set work directory
####################################################################################################
WORKDIR $HOME

####################################################################################################
# create shared volume but just folder (it is mounted later - ownership problem)
####################################################################################################
RUN mkdir logs
RUN touch logs/dockerVolumeHelper.tmp

####################################################################################################
# create the app user
####################################################################################################
RUN groupadd networkUsage && useradd networkUsage -r -g networkUsage

####################################################################################################
# install dependencies
####################################################################################################
# COPY requirements.txt ./
# RUN pip install --no-cache -r requirements.txt

####################################################################################################
# copy project
####################################################################################################
COPY . $HOME

####################################################################################################
# chown all the files to the networkUsage user
####################################################################################################
RUN chown -R networkUsage:networkUsage $HOME

####################################################################################################
# change to the networkUsage user
####################################################################################################
USER networkUsage

####################################################################################################
# mount volume point
####################################################################################################
VOLUME [ "/home/networkUsage/logs" ]

####################################################################################################
# start scraper script
####################################################################################################
CMD [ "python", "networkUsage.py" ]
