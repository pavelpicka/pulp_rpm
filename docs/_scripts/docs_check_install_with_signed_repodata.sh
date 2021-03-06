#!/usr/bin/env bash

# This script will execute the component scripts and ensure that the documented examples
# work as expected.

# From the _scripts directory, run with `source docs_check_install_with_signed_repodata.sh` (source
# to preserve the environment variables)
export REPO_NAME="signed-repo"
export DIST_NAME="signed-dist"

source base.sh

source repo_with_signing_service.sh "$REPO_NAME"
source remote.sh
source sync.sh
source publication.sh
source distribution.sh "$DIST_NAME"
source install_from_signed_repository.sh
