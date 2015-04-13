#!/usr/bin/python
import sys, argparse
import libvirt
import csv
import subprocess
import crypt
import os
import string
import tempfile
import shlex
import xml.etree.ElementTree as ET

#debian7 base
#root pass: lnsexam
#user: testuser
#pass: lnsexam

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
    interface = ""
    memory = 512
    net_template = None
    base = None
    
    def customize(self):
        password_hash = crypt.crypt(self.password)
        args = ['virt-customize']
        args += ['-a', self.disk_path]
        args += ['--delete', '/etc/network/interfaces']
        args += ['--hostname', self.hostname]
        args += ['--upload', '{}:{}'.format(self.render_interfaces_file(), "/etc/network/interfaces")]
        args += ['--run-command', 'useradd -m -s /bin/bash -p {} -U -G sudo {}'.format(shlex.quote(password_hash), self.username)]
        if "debian" in self.hostname:
            args += ['--root-password', "password:{}".format(self.password)]
            args += ['--install', 'sudo']
        subprocess.check_call(args)
            
    def install(self, libvirt_url):
        args = ['virt-install']
        args += ['-w', 'type=direct,source={},model=virtio'.format(self.interface)]
        args += ['--name', '{}-{}'.format(self.hostname, self.ip)]
        args += ['--memory', str(self.memory)]
        args += ['--disk', self.disk_path]
        args += ['--os-variant', 'debian7']
        args += ['--cpu', 'host']
        args += ['--import']
        args += ['--connect', libvirt_url]
        args += ['--noreboot']
        args += ['--noautoconsole']
        subprocess.check_call(args)
    
    def render_interfaces_file(self):
        template = string.Template(self.net_template)
        output = template.substitute(ip=self.ip, netmask=self.netmask, gateway=self.gateway, dns=self.dns)
        f = tempfile.NamedTemporaryFile(mode='w', delete=False)
        f.write(output)
        path = f.name
        f.close()
        return path

class Student:
    name = None
    surname = None
    machines = None
    
    def __repr__(self) :
        return 'Name: {}'.format(self.name)

def parse_students(path, interface, base_domains):
    f = open(path, 'r')
    reader = csv.DictReader(f)
    data = list()
    for row in reader:
        student = Student()
        student.name = row["Name"]
        student.surname = row["Surname"]
        
        machines = list()
        for domain in base_domains:
            vm = Machine()
            vm.username = row["Name"].lower()
            vm.ip = row["IP"]
            vm.netmask = row["Netmask"]
            vm.dns = row["DNS"]
            vm.gateway = row["Gateway"]
            vm.password = row["Surname"].lower()
            vm.base = domain
            vm.interface = interface
            machines.append(vm)
    
        student.machines = machines
        data.append(student)
        
    return data
    

def create_overlay_image(base_path, overlay_path):
    subprocess.check_call(['qemu-img', 'create', '-b', base_path, '-f', 'qcow2', overlay_path])

    
def get_disk_from_domain(domain):
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
    
    data = parse_students(args.students, args.interface, args.base_domains)
    for student in data:
        print(color.BOLD + "Student: {} {}".format(student.name, student.surname) + color.END)
        for machine in student.machines:
            machine.hostname = "{}-{}-{}".format(student.name, student.surname, machine.base)
            machine.domain = machine.hostname
            base_dir = os.path.split(base_images[machine.base])[0]
            new_img_path = os.path.join(base_dir, "{}.qcow2".format(machine.hostname))
            
            print(color.BOLD + "Creating image {}".format(new_img_path) + color.END)
            create_overlay_image(base_images[machine.base], new_img_path)
            machine.disk_path = new_img_path
            machine.net_template = debian_interfaces
            
            print(color.BOLD + "Customizing {}".format(machine.domain) + color.END)
            machine.customize()
            
            print(color.BOLD + "Installing {}".format(machine.domain) + color.END)
            machine.install(args.libvirt_url)
            

if __name__ == "__main__":
    main(sys.argv[1:])
    
    
    
