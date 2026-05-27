#!/bin/bash
git clone git@github.com:DINA-community/Project-Goetterdaemmerung.git
if [ -d "/home/ai/textmining2024matcher2026" ]; then
        rm -rf textmining2024matcher2026
fi
mv Project-Goetterdaemmerung textmining2024matcher2026
cd textmining2024matcher2026
git checkout matcher_2026
sed -i 's/CSAF_VENDORS=Siemens,Rockwell Automation,Schneider Electric/CSAF_VENDORS=Siemens/g' docker-run-api/docker-compose.yml
sed -i 's/docker-run-api/docker202426/g' docker-run-api/docker-compose.yml
sed -i 's/docker-run-api/docker202426/g' docker-run-api/Dockerfile
rm -rf .git
git clone https://github.com/cisagov/CSAF
mkdir -p resources/CSAF/csaf_files/OT/white
for year in {2010..2026}; do
  if [ -d "CSAF/csaf_files/OT/white/$year" ]; then
    cp -R "CSAF/csaf_files/OT/white/$year" "resources/CSAF/csaf_files/OT/white/$year"
  fi
done
rm -rf CSAF
mv docker-run-api docker202426
