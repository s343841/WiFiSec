import argparse
import subprocess
import json
import statistics
from tabulate import tabulate

def run_iperf_test(server_ip, protocol, num_runs):
    results = []
    for _ in range(num_runs):
        cmd = ['iperf3', '-c', server_ip, '-J', '-t', '10']  # Test di 10 secondi
        
        if protocol == 'udp':
            cmd.extend(['-u', '-b', '0'])  # Configurazione UDP
        
        print(f"\n[Esecuzione] {' '.join(cmd)}")  # Stampa il comando eseguito
        
        try:
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            data = json.loads(output)
            
            # Estrazione throughput in base al protocollo
            if protocol == 'tcp':
                thr = data['end']['sum_received']['bits_per_second'] / 1e6  # Converti in Mbps
            else:
                thr = data['end']['sum']['bits_per_second'] / 1e6
            
            results.append(thr)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante il test {protocol}: {e.output}")
    
    return results

def calculate_stats(data):
    if not data:
        return {'mean': 0, 'max': 0, 'min': 0, 'stddev': 0}
    
    return {
        'mean': statistics.mean(data),
        'max': max(data),
        'min': min(data),
        'stddev': statistics.stdev(data) if len(data) > 1 else 0
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Esegui test iperf3 TCP/UDP')
    parser.add_argument('server_ip', help='IP del server iperf3')
    args = parser.parse_args()

    # Esegui i test
    print("🔵 Esecuzione test TCP...")
    tcp_results = run_iperf_test(args.server_ip, 'tcp', 25)
    
    print("\n🔵 Esecuzione test UDP...")
    udp_results = run_iperf_test(args.server_ip, 'udp', 25)

    # Calcola statistiche
    tcp_stats = calculate_stats(tcp_results)
    udp_stats = calculate_stats(udp_results)

    # Crea tabella
    table = [
        ["TCP", tcp_stats['mean'], tcp_stats['max'], tcp_stats['min'], tcp_stats['stddev']],
        ["UDP", udp_stats['mean'], udp_stats['max'], udp_stats['min'], udp_stats['stddev']]
    ]

    headers = ["Protocollo", "Media (Mbps)", "Max (Mbps)", "Min (Mbps)", "Dev Std"]
    
    print("\n📊 Risultati:")
    print(tabulate(table, headers=headers, tablefmt="grid", floatfmt=".2f"))
