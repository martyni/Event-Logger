#!/bin/bash
export ORIGINAL_DIR=$(pwd)
ROOT_PROJECT_DIR=$(git rev-parse --show-toplevel)
OUTPUT_FILE=/tmp/output
date> ${OUTPUT_FILE}

cd $ROOT_PROJECT_DIR || return
source scripts/common.sh

echo -e ${YELLOW}Running tests from  ${RUN_DIR}${NO_COLOUR}

python_install () {
  CURRENT_TEST=python_install
  echo -e ${YELLOW} Starting Python Install ${NO_COLOUR}
  pip install .[dev]
}


fail () {
   if [[ ${CURRENT_TEST} ]]; then
       echo fail ${CURRENT_TEST}
   fi
   return 1
   exit 1
}
python_test () {
  CURRENT_TEST=E2E Python
  URL=localhost:5000/event
  echo -e ${YELLOW} Starting Python Test ${NO_COLOUR}
  pgrep flask | xargs kill 2>/dev/null
  flask --app=eventlogger.app:app run &
  sleep 1
  (curl -I --fail ${URL} || fail ) && (curl --fail ${URL}  | jq . || fail) && (pytest || fail && (pgrep flask | xargs kill))
}

linting_test () {
  CURRENT_TEST=Linting
  echo -e ${YELLOW} Starting Linting Test ${NO_COLOUR}
  autopep8 --recursive --in-place --aggressive --aggressive .
  pylint  --persistent=no $(git ls-files '*.py') || fail
}

build_test () {
  CURRENT_TEST=Build
  echo -e ${YELLOW} Starting Build Test ${NO_COLOUR} in $(pwd)
  ${RUN_DIR}/build.sh || fail
}

run_test () {
  CURRENT_TEST=Run
  echo -e ${YELLOW} Starting Run Test ${NO_COLOUR}
  ${RUN_DIR}/run.sh || fail
  echo -e ${YELLOW} Finished Run Test ${NO_COLOUR}
}

all_tests_pass () {
  echo -e ${GREEN} All tests passed ${NO_COLOUR}
  ${RUN_DIR}/increment.sh && ${RUN_DIR}/build.sh || fail 
}

python_install && python_test && linting_test && build_test && run_test  || export CURRENT_TEST='' fail && all_tests_pass
