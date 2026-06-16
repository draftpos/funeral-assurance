#!/bin/bash

echo "==========================================="
echo " Deploying Funeral Assurance Module Update"
echo "==========================================="

# 1. Pull the latest code
echo "-> Pulling latest code from git..."
git pull origin main

# 2. Restart the Odoo Service
# NOTE: If your Odoo service is named something else (like odoo17 or odoo-server), change it here!
echo "-> Restarting Odoo Service to load new Python models..."
sudo systemctl restart odoo

echo "==========================================="
echo " Deployment successful!"
echo " Please log into Odoo, go to Apps, and click 'Upgrade' on Funeral Assurance."
echo "==========================================="
