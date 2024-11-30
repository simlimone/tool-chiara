#!/bin/bash

# Colori per l'output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Sei sicuro di voler aggiornare il progetto? (s/n)${NC}"
read -r risposta

if [[ "$risposta" != "s" && "$risposta" != "S" ]]; then
    echo -e "${RED}Aggiornamento annullato.${NC}"
    exit 0
fi

echo -e "${GREEN}Inizio aggiornamento del progetto...${NC}"

# Estrai l'ultima versione dal repository remoto
git fetch origin
git pull origin main

if [ $? -ne 0 ]; then
    echo -e "${RED}Errore durante l'aggiornamento del repository.${NC}"
    exit 1
fi

echo -e "${GREEN}Aggiornamento completato con successo!${NC}"

# Esegui eventuali script di installazione o aggiornamento delle dipendenze
echo -e "${GREEN}Installazione delle dipendenze...${NC}"
if [ -f "setup.ps1" ]; then
    pwsh setup.ps1
elif [ -f "setup.sh" ]; then
    bash setup.sh
else
    echo -e "${RED}Nessuno script di installazione trovato.${NC}"
    exit 1
fi

echo -e "${GREEN}Aggiornamento e installazione delle dipendenze completati!${NC}"
