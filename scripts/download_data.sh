#!/usr/bin/env sh
set -eu
mkdir -p data
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
