#!/bin/bash
git clone git@github.com:DINA-community/Project-Goetterdaemmerung.git
if [ -d "/home/ai/textmining2024matcher2024" ]; then
        rm -rf textmining2024matcher2024
fi
mv Project-Goetterdaemmerung textmining2024matcher2024
cd textmining2024matcher2024
git checkout master2024
sed -i 's/127.0.0.1:5000:5000/127.0.0.1:4999:5000/g' docker-run-api/docker-compose.yml
rm -rf .git
git clone https://github.com/cisagov/CSAF
mkdir -p resources/CSAF/csaf_files/OT/white
cp -R CSAF/csaf_files/OT/white/2024 resources/CSAF/csaf_files/OT/white/2024
cp -R CSAF/csaf_files/OT/white/2025 resources/CSAF/csaf_files/OT/white/2025
cp -R CSAF/csaf_files/OT/white/2026 resources/CSAF/csaf_files/OT/white/2026
rm -rf CSAF
cd ..
