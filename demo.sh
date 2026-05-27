#!/bin/bash
git clone https://github.com/cisagov/CSAF
mkdir -p resources/CSAF/csaf_files/OT/white
for year in {2024..2026}; do
  if [ -d "CSAF/csaf_files/OT/white/$year" ]; then
    cp -R "CSAF/csaf_files/OT/white/$year" "resources/CSAF/csaf_files/OT/white/$year"
  fi
done
rm -rf CSAF
cd docker-run-api
docker-compose up