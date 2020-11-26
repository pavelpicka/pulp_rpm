#!/usr/bin/env bash
# coding=utf-8

# WARNING: DO NOT EDIT!
#
# This file was generated by plugin_template, and is managed by it. Please use
# './plugin-template --github pulp_rpm' to update this file.
#
# For more info visit https://github.com/pulp/plugin_template

# make sure this script runs at the repo root
cd "$(dirname "$(realpath -e "$0")")"/../../..
REPO_ROOT="$PWD"

set -mveuo pipefail

source .github/workflows/scripts/utils.sh

export POST_SCRIPT=$PWD/.github/workflows/scripts/post_script.sh
export POST_DOCS_TEST=$PWD/.github/workflows/scripts/post_docs_test.sh
export FUNC_TEST_SCRIPT=$PWD/.github/workflows/scripts/func_test_script.sh

# Needed for both starting the service and building the docs.
# Gets set in .github/settings.yml, but doesn't seem to inherited by
# this script.
export DJANGO_SETTINGS_MODULE=pulpcore.app.settings
export PULP_SETTINGS=$PWD/.ci/ansible/settings/settings.py

if [[ "$TEST" = "docs" || "$TEST" = "publish" ]]; then
  cd docs
  make PULP_URL="http://pulp" html
  cd ..

  if [ -f $POST_DOCS_TEST ]; then
    source $POST_DOCS_TEST
  fi
  exit
fi

if [[ "$TEST" == "plugin-from-pypi" ]]; then
  COMPONENT_VERSION=$(http https://pypi.org/pypi/pulp-rpm/json | jq -r '.info.version')
  git checkout ${COMPONENT_VERSION} -- pulp_rpm/tests/
fi

cd ../pulp-openapi-generator

./generate.sh pulpcore python
pip install ./pulpcore-client
./generate.sh pulp_rpm python
pip install ./pulp_rpm-client
cd $REPO_ROOT

if [[ "$TEST" = 'bindings' || "$TEST" = 'publish' ]]; then
  python $REPO_ROOT/.github/workflows/scripts/test_bindings.py
  cd ../pulp-openapi-generator
  if [ ! -f $REPO_ROOT/.github/workflows/scripts/test_bindings.rb ]
  then
    exit
  fi

  rm -rf ./pulpcore-client

  ./generate.sh pulpcore ruby 0
  cd pulpcore-client
  gem build pulpcore_client
  gem install --both ./pulpcore_client-0.gem
  cd ..
  rm -rf ./pulp_rpm-client

  ./generate.sh pulp_rpm ruby 0

  cd pulp_rpm-client
  gem build pulp_rpm_client
  gem install --both ./pulp_rpm_client-0.gem
  cd ..
  ruby $REPO_ROOT/.github/workflows/test_bindings.rb
  exit
fi

cat unittest_requirements.txt | cmd_stdin_prefix bash -c "cat > /tmp/unittest_requirements.txt"
cmd_prefix pip3 install -r /tmp/unittest_requirements.txt

# check for any uncommitted migrations
echo "Checking for uncommitted migrations..."
cmd_prefix bash -c "django-admin makemigrations --check --dry-run"

# Run unit tests.
cmd_prefix bash -c "PULP_DATABASES__default__USER=postgres django-admin test --noinput /usr/local/lib/python3.7/site-packages/pulp_rpm/tests/unit/"

# Run functional tests
export PYTHONPATH=$REPO_ROOT:$REPO_ROOT/../pulpcore${PYTHONPATH:+:${PYTHONPATH}}

if [ -f $FUNC_TEST_SCRIPT ]; then
  source $FUNC_TEST_SCRIPT
else
    pytest -v -r sx --color=yes --pyargs pulp_rpm.tests.functional
fi

if [ -f $POST_SCRIPT ]; then
  source $POST_SCRIPT
fi
