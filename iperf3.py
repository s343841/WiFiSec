import argparse
import subprocess
import json
import statistics
from tabulate import tabulate
from time import sleep
import sys

# Funzione per determinare il comando da utilizzare (.\iperf3.exe oppure iperf3)
def get_iperf_command():
    # Prova prima con .\iperf3.exe (Windows)
    try:
        subprocess.check_output([".\\iperf3.exe", "--version"], text=True, stderr=subprocess.STDOUT)
        return ".\\iperf3.exe"
    except Exception:
        # Se fallisce, usa iperf3
        return "iperf3"

def run_iperf_test(server_ip, protocol, bandwidth, iperf_cmd, num_runs=10):
    results = []
    
    for i in range(num_runs):
        # Comando base
        cmd = [iperf_cmd, '-c', server_ip, '-J', '-t', '10']  # test di 10 secondi
        
        if protocol == 'udp':
            cmd.extend(['-u', '-b', bandwidth, '-l', '1472'])  # impostazioni UDP
            sleep(2)  # Attesa di 2 secondi per evitare conflitti tra test
        
        log_line = f"\n[Esecuzione {i+1}/{num_runs}] {' '.join(cmd)}"
        print(log_line)
        output_lines.append(log_line)
        
        try:
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            
            # Trova l'inizio del JSON nell'output
            json_start = output.find('{')
            if json_start != -1:
                output = output[json_start:]
            
            try:
                data = json.loads(output)
                
                # Estrai throughput medio dal ricevitore
                if protocol == 'tcp':
                    thr = data['end']['sum_received']['bits_per_second'] / 1e6  # Mbps
                elif protocol == 'udp':
                    thr = data['end']['sum']['bits_per_second'] / 1e6  # Mbps
                
                results.append(thr)
            except json.JSONDecodeError:
                error_msg = "❌ Errore decodifica JSON. Output ricevuto:\n" + output
                print(error_msg)
                output_lines.append(error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Errore durante iperf3: {e.output}"
            print(error_msg)
            output_lines.append(error_msg)
    
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
    output_lines = []  # lista per salvare l'output da scrivere nel file
    
    parser = argparse.ArgumentParser(description='Esegui test iperf3 TCP/UDP')
    parser.add_argument('server_ip', help='IP del server iperf3')
    parser.add_argument('--bandwidth', default='400M', help='Larghezza di banda per il test UDP (es. 400M)')
    parser.add_argument('--protocol', choices=['tcp', 'udp', 'both'], default='both',
                        help="Protocollo per il test: 'tcp', 'udp', o 'both' (default è 'both')")
    args = parser.parse_args()
    
    iperf_cmd = get_iperf_command()
    print(f"Utilizzo comando iperf3: {iperf_cmd}")
    output_lines.append(f"Utilizzo comando iperf3: {iperf_cmd}\n")
    
    results_summary = []
    
    # Test TCP
    if args.protocol in ['tcp', 'both']:
        print("🔵 Esecuzione test TCP...")
        output_lines.append("🔵 Esecuzione test TCP...\n")
        tcp_results = run_iperf_test(args.server_ip, 'tcp', args.bandwidth, iperf_cmd)
        stats_tcp = calculate_stats(tcp_results)
        results_summary.append(["TCP", f"{stats_tcp['mean']:.2f}", f"{stats_tcp['max']:.2f}",
                                f"{stats_tcp['min']:.2f}", f"{stats_tcp['stddev']:.2f}"])
    
    # Test UDP
    if args.protocol in ['udp', 'both']:
        print("\n🔵 Esecuzione test UDP...")
        output_lines.append("\n🔵 Esecuzione test UDP...\n")
        udp_results = run_iperf_test(args.server_ip, 'udp', args.bandwidth, iperf_cmd)
        stats_udp = calculate_stats(udp_results)
        results_summary.append(["UDP", f"{stats_udp['mean']:.2f}", f"{stats_udp['max']:.2f}",
                                f"{stats_udp['min']:.2f}", f"{stats_udp['stddev']:.2f}"])
    
    # Creazione della tabella con i risultati
    table_header = ["Protocollo", "Media (Mbps)", "Max (Mbps)", "Min (Mbps)", "Dev Std"]
    table = tabulate(results_summary, headers=table_header, tablefmt="grid")
    
    results_output = "\n📊 Risultati:\n" + table
    print(results_output)
    output_lines.append(results_output)
    
    # Salvataggio dell'output in output.txt
    try:
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        print("\n✅ Output salvato in output.txt")
    except Exception as e:
        print(f"❌ Errore durante il salvataggio dell'output: {e}")
