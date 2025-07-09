import numpy as np
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.log import setLogLevel
import time
import subprocess
from topology.network_simulator import RealNetworkSimulator
class MininetNetworkEnvironment:
    def __init__(self):
        setLogLevel('info')
        self.simulator = RealNetworkSimulator()
        self.net = Mininet(controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633))
        self.action_space = 8  # Increased action space for real network operations
        self.state_space = 80  # Fixed state vector size
        self.episode_length = 50
        self.current_step = 0
        self.baseline_performance = 0
        
        # Action mapping
        self.actions = {
            0: self.restart_failed_switch,
            1: self.reroute_traffic,
            2: self.adjust_link_bandwidth,
            3: self.restart_host_service,
            4: self.clear_flow_tables,
            5: self.load_balance_traffic,
            6: self.reduce_packet_loss,
            7: self.do_nothing
        }
    
    def reset(self):
        """Reset environment for new episode"""
        if self.net:
            self.simulator.stop_network()

        self.net = self.simulator.create_enterprise_topology()
        self.simulator.start_network()

        time.sleep(5)

        print("[DEBUG] Dumping host interfaces:")
        for host_name in ['web1', 'db1', 'pc1']:
            host = self.net.get(host_name)
            print(f"{host_name}:")
            print(host.cmd("ifconfig"))

        self.baseline_performance = self.simulator.calculate_network_performance()
        self.current_step = 0
        return self.simulator.get_network_state_vector()

    
    def step(self, action):
        """Execute one step in the environment"""
        prev_performance = self.simulator.calculate_network_performance()
        
        # Execute healing action
        action_reward = self.actions[action]()
        
        # Inject random failures (simulate dynamic network)
        if np.random.random() < 0.15:  # 15% chance of new failure
            failure_types = ['link_failure', 'congestion', 'high_latency', 'packet_loss']
            failure_type = np.random.choice(failure_types)
            self.simulator.inject_network_failure(failure_type)
        
        # Wait for network to react
        time.sleep(3)
        
        # Get new state and performance
        new_state = self.simulator.get_network_state_vector()
        new_performance = self.simulator.calculate_network_performance()
        
        # Calculate reward
        performance_improvement = new_performance - prev_performance
        reward = action_reward + performance_improvement * 0.5
        
        # Bonus for maintaining high performance
        if new_performance > 80:
            reward += 10
        
        # Penalty for very low performance
        if new_performance < 30:
            reward -= 10
        
        self.current_step += 1
        done = self.current_step >= self.episode_length
        
        info = {
            'performance': new_performance,
            'improvement': performance_improvement,
            'baseline': self.baseline_performance
        }
        
        return new_state, reward, done, info
    
    def restart_failed_switch(self):
        """Restart failed switches"""
        try:
            # Find failed switches and restart them
            for switch in self.simulator.switches:
                # Check if switch is responding
                result = subprocess.run(f"sudo ovs-ofctl show {switch.name}", 
                                      shell=True, capture_output=True)
                if result.returncode != 0:
                    # Switch is failed, restart it
                    switch.start(self.net.controllers)
                    return 20
            return 0
        except Exception as e:
            print(f"Switch restart error: {e}")
            return -5
    
    def reroute_traffic(self):
        """Implement traffic rerouting using OpenFlow"""
        try:
            # Install backup flows for better path diversity
            switches = ['s1', 's2', 's3', 's4']
            for switch in switches:
                # Add flow for alternate path
                cmd = f"sudo ovs-ofctl -O OpenFlow13 add-flow {switch} " \
                      f"priority=100,ip,nw_dst=10.0.1.0/24,actions=output:2"
                subprocess.run(cmd, shell=True)
            return 15
        except Exception as e:
            print(f"Rerouting error: {e}")
            return -3
    
    def adjust_link_bandwidth(self):
        """Adjust link bandwidth to reduce congestion"""
        try:
            # Use traffic control to manage bandwidth
            links = ['s1-eth1', 's2-eth1', 's3-eth1']
            for link in links:
                # Remove existing qdisc and add new one
                subprocess.run(f"sudo tc qdisc del dev {link} root", shell=True)
                subprocess.run(f"sudo tc qdisc add dev {link} root handle 1: htb default 30", shell=True)
                subprocess.run(f"sudo tc class add dev {link} parent 1: classid 1:1 htb rate 100mbit", shell=True)
            return 12
        except Exception as e:
            print(f"Bandwidth adjustment error: {e}")
            return -2
    
    def restart_host_service(self):
        """Restart services on hosts"""
        try:
            # Restart network services on hosts
            hosts = ['web1', 'web2', 'db1']
            for host_name in hosts:
                host = self.net.get(host_name)
                if host:
                    host.cmd('sudo systemctl restart networking')
            return 10
        except Exception as e:
            print(f"Service restart error: {e}")
            return -2
    
    def clear_flow_tables(self):
        """Clear and rebuild flow tables"""
        try:
            for switch in self.simulator.switches:
                # Clear existing flows
                subprocess.run(f"sudo ovs-ofctl -O OpenFlow13  del-flows {switch.name}", shell=True)
                # Let controller reinstall basic flows
                time.sleep(2)
            return 8
        except Exception as e:
            print(f"Flow table clear error: {e}")
            return -3
    
    def load_balance_traffic(self):
        """Implement simple load balancing"""
        try:
            # Add group table entries for load balancing
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-group s1 " \
                  "group_id=1,type=select,bucket=output:2,bucket=output:3"
            subprocess.run(cmd, shell=True)
            
            # Add flow to use group table
            cmd = "sudo ovs-ofctl -O OpenFlow13 add-flow s1 " \
                  "priority=200,ip,nw_dst=10.0.1.0/24,actions=group:1"
            subprocess.run(cmd, shell=True)
            return 18
        except Exception as e:
            print(f"Load balancing error: {e}")
            return -2
    
    def reduce_packet_loss(self):
        """Reduce packet loss by adjusting queue parameters"""
        try:
            # Adjust queue lengths and parameters
            interfaces = ['s1-eth1', 's1-eth2', 's2-eth1', 's2-eth2']
            for iface in interfaces:
                # Remove existing packet loss
                subprocess.run(f"sudo tc qdisc del dev {iface} root", shell=True)
                # Add optimized qdisc
                subprocess.run(f"sudo tc qdisc add dev {iface} root fq_codel", shell=True)
            return 14
        except Exception as e:
            print(f"Packet loss reduction error: {e}")
            return -1
    
    def do_nothing(self):
        """No action - sometimes the best choice"""
        return -1
    
    def cleanup(self):
        """Cleanup network resources"""
        if self.simulator:
            self.simulator.stop_network()