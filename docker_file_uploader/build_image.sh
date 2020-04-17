#!/usr/bin/env bash

image=apluslms-file-transfer-client

docker build --rm -t ${image} .

#docker tag ${image} qianqianq/${image}:latest
#docker push qianqianq/${image}:latest