ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3
RUN apk add py3-pip
RUN pip3 install paho-mqtt
RUN pip3 install requests
RUN pip3 install PyYAML

COPY mediola2mqtt.py /
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
