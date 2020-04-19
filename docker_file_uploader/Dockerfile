FROM apluslms/service-base:python3-1.5

WORKDIR /app

ENV TZ=Europe/Helsinki

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt ./
RUN pip3 install -r  requirements.txt

RUN pip3 install git+https://github.com/apluslms/apluslms-file-transfer.git

COPY . ./

ENTRYPOINT ["python3", "/app/uploader.py"]