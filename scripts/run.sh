#!/bin/bash -x
source scripts/common.sh


test_fail () {
   container=$1
   docker ps
   docker logs ${container}
   return 1
}

docker stop $(docker ps | awk  "/${DOCKER_REPO}\/${NAME}/{print \$1}")
docker run ${DOCKER_FLAGS} ${DOCKER_REPO}/${NAME}:${VERSION} 
sleep 1
docker ps | awk /eventlogger/'{print $10}' | awk -F '->' '{ print $1}' | awk -F ':' '{print $2}'
export TMP_PORT=$(docker ps | awk /eventlogger/'{print $10}' | awk -F '->' '{ print $1}' | awk -F ':' '{print $2}' | xargs )
container_name=$(docker ps | awk  "/${DOCKER_REPO}\/${NAME}/{print \$1}")
for i in {1..5}; do
	
        echo -e ${YELLOW}Attempt $i of 5 ${NO_COLOUR}
	curl --fail -i --max-time 10 -H "Content-Type: application/json" --data '{"user":"alex","message":"Hi everyone! Alex here" }' https://${NAME}.${DOMAIN}:${TMP_PORT}/event || test_fail ${container_name} || break
        docker stop ${container_name} &
	exit 0
        echo End of Run test
done
echo -e ${RED} MAX 5 retries failed${NO_COLOUR}
exit 1
