import sys
import time
import random
import logging
from scapy.all import IP, TCP, UDP, send, conf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StressTest")

def generate_traffic(interface, duration_seconds=60, intensity="high"):
    """
    Simulate various types of network traffic to stress test the IDS.
    """
    logger.info(f"Starting stress test on {interface} for {duration_seconds} seconds...")
    
    start_time = time.time()
    packet_count = 0
    
    # Target (could be anything, we just want to generate flows)
    target_ip = "192.168.1.100"
    
    # Variety of sources
    sources = [f"10.0.0.{i}" for i in range(1, 255)]
    
    # Attack types
    attack_types = ["syn_flood", "port_scan", "udp_flood", "mixed"]
    
    try:
        while time.time() - start_time < duration_seconds:
            attack = random.choice(attack_types)
            src = random.choice(sources)
            
            if attack == "syn_flood":
                # Rapid SYN packets to a single port
                dst_port = 80
                packets = [IP(src=src, dst=target_ip)/TCP(sport=random.randint(1024, 65535), dport=dst_port, flags="S") for _ in range(50)]
                send(packets, iface=interface, verbose=False)
                packet_count += 50
                
            elif attack == "port_scan":
                # Packets to many different ports
                dst_ports = random.sample(range(1, 1024), 20)
                packets = [IP(src=src, dst=target_ip)/TCP(sport=random.randint(1024, 65535), dport=p, flags="S") for p in dst_ports]
                send(packets, iface=interface, verbose=False)
                packet_count += 20
                
            elif attack == "udp_flood":
                # UDP packets
                dst_port = random.randint(1, 65535)
                packets = [IP(src=src, dst=target_ip)/UDP(sport=random.randint(1024, 65535), dport=dst_port) for _ in range(50)]
                send(packets, iface=interface, verbose=False)
                packet_count += 50
                
            elif attack == "mixed":
                # Random normal-looking traffic
                dst_port = random.choice([80, 443, 22, 53])
                packets = [IP(src=src, dst=target_ip)/TCP(sport=random.randint(1024, 65535), dport=dst_port, flags="PA") for _ in range(10)]
                send(packets, iface=interface, verbose=False)
                packet_count += 10
            
            if intensity == "high":
                pass # No sleep
            else:
                time.sleep(0.1)
                
            if packet_count % 500 == 0:
                logger.info(f"Sent {packet_count} packets...")
                
    except KeyboardInterrupt:
        logger.info("Stress test interrupted.")
    
    end_time = time.time()
    logger.info(f"Stress test complete. Sent {packet_count} packets in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stress_test.py <interface>")
        sys.exit(1)
        
    interface = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    generate_traffic(interface, duration)
