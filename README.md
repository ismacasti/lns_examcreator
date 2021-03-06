# lns_examcreator
Creates virtual machines for Linux Network Servers exams

# Requirements
This script needs a quite recent version of the libguestfs package. The packages found in the Ubuntu 14.04 are too old; this was tested succesfully in Arch Linux and Fedora Server 21. The script uses virt-install and virt-customize.
It also requires Python 3 and the libvirt Python3 bindings. It might work in Python 2, but it has not been tested.

A base virtual machine installed in the libvirt server should be created before hand, with the software you need already installed. It is recommended to run 'virt-sysprep' on the base images before using them with this script.

# Limitations
The current version only supports Debian 7 and Ubuntu 14.04. It might work on older or newer versions of Debian-based systems, but it was not tested.

# Instructions
First you need to have a base virtual machine created on the libvirt server. A just finished image with no software installed is enough. 
The script requires at least 4 parameters:
1. the file path of the CSV file with the student data (example in data.csv file)
2. the URL of the libvirt server. Local machine URL is qemu:///system 
3. the host interface name the virtual machines will use to connect to the network (using macvtap).
4. list of names of the base images, for example 'ubuntu1404base' and 'debian7base'.

The script will create a personalized virtual machine for each student and each base image. All the virtual machines of the same student will have the same IP address, so do not start them at the same time.

It might work running as a normal user, but it needs permissions on libvirt server and to write files in the libvirt image folder. You can run it as root to be safe.

When the script finished you can find all the students domains in the libvirt server, ready to be launched and used. The username will be the student's name and the password will be the student's surname, both in lowercase.

# How it works
The script will create an overlay qemu image for each student and each base image, and then it will configure it based on the information in the students csv file. This is accomnplished using the qemu utilities, the libvirt API and the libguestfs utilities. 
