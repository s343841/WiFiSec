#!/bin/bash

# Imposta i parametri
SERVER="192.168.1.100"  # Sostituisci con l'IP del server iperf3
DURATION=50             # Durata totale del test in secondi

# Inizia la trasmissione con variazioni di bitrate
for i in {1..3}; do
    echo "Trasmissione ad alta velocità..."
    iperf3 -c $SERVER -u -b 1G -t 7 &  # Trasmissione a 1 Gbps per 7 secondi
    sleep 7

    echo "Calo del bitrate a 750 Mbps..."
    iperf3 -c $SERVER -u -b 750M -t 3 &  # Trasmissione a 750 Mbps per 3 secondi
    sleep 3

    echo "Stop per 3 secondi..."
    sleep 3  # Simula la pausa nella trasmissione
done

echo "Test completato!"
