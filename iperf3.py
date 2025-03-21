import argparse
import subprocess
import json
import statistics
from tabulate import tabulate
from time import sleep

def run_iperf_test(server_ip, protocol, bandwidth, num_runs=10):
    results = []
    
    for _ in range(num_runs):
        cmd = ['./iperf3', '-c', server_ip, '-J', '-t', '10']  # 10 sec test
        
        if protocol == 'udp':
            cmd.extend(['-u', '-b', bandwidth, '-l', '1472'])  # UDP settings
            sleep(10)  # Attendi per evitare conflitti tra test
        
        print(f"\n[Esecuzione] {' '.join(cmd)}")
        
        try:
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            
            json_start = output.find('{')  # Trova l'inizio del JSON
            if json_start != -1:
                output = output[json_start:]
            
            try:
                data = json.loads(output)
                
                # Estrai throughput medio dal ricevitore
                if protocol == 'tcp':
                    thr = data['end']['sum_received']['bits_per_second'] / 1e6  # Mbps
                else:
                    thr = data['end']['sum']['bits_per_second'] / 1e6  # UDP Mbps
                
                results.append(thr)
            
            except json.JSONDecodeError:
                print("❌ Errore decodifica JSON. Output ricevuto:")
                print(output)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante iperf3: {e.output}")
    
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
    parser.add_argument('--bandwidth', default='400M', help='Larghezza di banda per il test UDP (es. 400M)')
    args = parser.parse_args()

    print("🔵 Esecuzione test TCP...")
    tcp_results = run_iperf_test(args.server_ip, 'tcp', args.bandwidth)
    
    print("\n🔵 Esecuzione test UDP...")
    udp_results = run_iperf_test(args.server_ip, 'udp', args.bandwidth)
    
    tcp_stats = calculate_stats(tcp_results)
    udp_stats = calculate_stats(udp_results)
    
    table = [
        ["TCP", tcp_stats['mean'], tcp_stats['max'], tcp_stats['min'], tcp_stats['stddev']],
        ["UDP", udp_stats['mean'], udp_stats['max'], udp_stats['min'], udp_stats['stddev']]
    ]
    
    headers = ["Protocollo", "Media (Mbps)", "Max (Mbps)", "Min (Mbps)", "Dev Std"]
    
    print("\n📊 Risultati:")
    print(tabulate(table, headers=headers, tablefmt="grid", floatfmt=".2f"))
