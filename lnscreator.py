#!/usr/bin/python
import sys, argparse
import libvirt
import csv
import subprocess
import crypt
import os

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


debian_interfaces = """
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto eth0
iface eth0 inet static
address $ip
netmask $netmask
gateway $gateway
nameserver $dns
"""
network_configs = dict()
network_configs['debian7'] = debian_interfaces
network_configs['ubuntu1404'] = debian_interfaces


class Machine():
    hostname = None
    password = None
    username = None
    ip = None
    netmask = None 
    gateway = None
    dns = None
    system = None
    disk_path = None
    domain = None
    interface = "enp4s0"
    memory = 512
    
    def customize(self, config_path):
        password_hash = crypto.crypto(password)
        args = ['virt-customize']
        args += ['-a', disk_path]
        args += ['--delete', '/etc/network/interfaces']
        args += ['--hostname', hostname]
        args += ['--copy-in', '{}:{}'.format(config_path, "/etc/network/interfaces")]
        args += ['--run-command', 'useradd -m -p {} -U -G sudo {}'.format(password, username)]
        subprocess.check_call(args)
            
    def install(self, libvirt_url):
        args = ['virt-install']
        args += ['-w', 'type=direct,source={},model=virtio'.format(interface)]
        args += ['--name', '{}@{}({})'.format(hostname, ip, system)]
        args += ['--memory', memory]
        args += ['--disk', disk_path]
        args += ['--os-variant', 'debian7']
        args += ['--cpu', 'host']
        args += ['--import']
        args += ['--connect', libvirt_url]
        subprocess.check_call(args)
    

class Student:
    name = None
    surname = None
    machine = None
    
    def __repr__(self) :
        return 'Name: {}'.format(self.name)

def parse_students(path):
    f = open(path, 'r')
    reader = csv.DictReader(f)
    data = list()
    for row in reader:
        student = Student()
        student.name = row["Name"]
        student.surname = row["Surname"]
        
        vm = Machine()
        vm.username = row["Name"].lower()
        vm.ip = row["IP"]
        vm.netmask = row["Netmask"]
        vm.dns = row["DNS"]
        vm.gateway = row["Gateway"]
        vm.password = row["Name"]
    
        student.machine = vm
        data.append(student)
    
    return data
    

def create_overlay_image(base_path, overlay_path):
    subprocess.check_call(['qemu-img', 'create', '-b', base_path, '-f', 'qcow2', overlay_path])

def sysprep_image(img_path):
    args = ["virt-sysprep"]
    args += ["-a", img_path]
    subprocess.check_call(args)
    
import string
import tempfile
def render_interfaces_file(machine, text):
    template = string.Template(text)
    output = template.substitute(ip=machine.ip, netmask=machine.netmask, gateway=machine.gateway, dns=machine.dns)
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    f.write(output)
    path = f.name
    f.close()
    return path

def create_overlay_clone(machine, student):
    network_config_file = render_interfaces_file(machine, network_configs[machine.system])
    
def get_disk_from_domain(domain):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(domain.XMLDesc())
    source_element = root.find(".//disk[@device='disk']/source")
    path = source_element.items()[0][1]
    return path
    
def main(argv):
    parser = argparse.ArgumentParser(description="Automatically create exam machines")
    parser.add_argument("students", help="CSV file with student and machine info")
    parser.add_argument("libvirt_url", help="The libVirt URL where the changes will be made")
    parser.add_argument("interface", help="The host interface the domains will use")
    parser.add_argument("base_domains", help="List of base domains the script will use", nargs='+')
    
    args = parser.parse_args()
    conn = libvirt.open(args.libvirt_url)
    print(color.BOLD + "Connected to server: {}".format(conn.getHostname()) + color.END)
    base_images = dict()
    print("List of base images:")
    for i in args.base_domains:
        domain = conn.lookupByName(i)
        path = get_disk_from_domain(domain)
        base_images[i] = path
        print("{} → {}".format(i,path))
    
    data = parse_students(args.students)
    for student in data:
        print(color.BOLD + "Setting up {} {}".format(student.name, student.surname) + color.END)
        for base_domain in base_images:
            student.machine.hostname = "{}-{}-{}".format(student.name, student.surname, base_domain)
            student.machine.domain = student.machine.hostname
            base_dir = os.path.split(base_images[base_domain])[0]
            new_img_path = os.path.join(base_dir, "{}.qcow2".format(student.machine.hostname))
            create_overlay_image(base_images[base_domain], new_img_path)
            student.machine.disk_path = new_img_path
            

if __name__ == "__main__":
    main(sys.argv[1:])
    
    
    
