#!/usr/bin/python


class Machine:
    hostname = None
    password = None
    username = None
    ip = None
    netmask = None 
    
class Student:
    name = None
    surname = None

    

import sys, argparse
import libvirt
def main(argv):
    parser = argparse.ArgumentParser(description="Automatically create exam machines")
    parser.add_argument("students", help="CSV file with student and machine info")
    parser.add_argument("libvirt_url", help="The libVirt URL where the changes will be made")
    
    args = parser.parse_args()


if __name__ == "__main__":
    main(sys.argv[1:])
    conn = libvirt.open(libvirt_url)
    print("Connected to server: %s", conn.getURI())
    
    
