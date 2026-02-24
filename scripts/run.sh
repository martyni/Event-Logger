#!/bin/bash
source scripts/common.sh



docker stop $(docker ps | awk  "/${DOCKER_REPO}\/${NAME}/{print \$1}")
docker run ${DOCKER_FLAGS} ${DOCKER_REPO}/${NAME}:${VERSION} 
sleep 1
docker ps | awk /eventlogger/'{print $10}' | awk -F '->' '{ print $1}' | awk -F ':' '{print $2}'
export TMP_PORT=$(docker ps | awk /eventlogger/'{print $10}' | awk -F '->' '{ print $1}' | awk -F ':' '{print $2}' | xargs )
curl --fail -i -H "Content-Type: application/json" --data '{"user":"alex","message":"Hi everyone! Alex here" }' https://${NAME}.${DOMAIN}:${TMP_PORT}/event || exit 1
docker stop $(docker ps | awk  "/${DOCKER_REPO}\/${NAME}/{print \$1}")&
echo End of Run test
