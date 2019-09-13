import json
import paramiko
import re
import logging
import socket
import os

config_file = 'basic.cfg'

'''
	valid_ip 	- 	This procedure will validate IP address
	Parameters  - 	Ip_address
	Return :		
		True on valid Ip_address
		False on invalid Ip_address

'''
def valid_ip(address):
    try: 
        socket.inet_aton(address)
        return True
    except:
        return False
'''	 
	Procedure to connect to remote host with given parameters and returning the shell handle
	
	invoked shell handle will be used to execute further commands
	handle will be set to None in case fails
	
	Return Value: client shell handle in case successful
				  None in case of failure
        

'''
def connect_host(ip_address, username, password):
    
    print('Connect to host : {}'.format(ip_address))
    print('with entered User Name {}'.format(username))
    print('and with entered Password {}'.format(password))
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip_address, username=username, password=password,look_for_keys=False, allow_agent=False)
        print("Successfully connected to the host")
        return client
    except Exception as inst:
        print('\nCaught exception while connecting and getting invoke shell handle\n')
        print(type(inst))
        print(inst.args)
        print(inst)
        return None
'''
	invoked shell handle will be used to execute further commands
	handle will be set to None in case fails
    Execute one command at a time on SUT    
    Assumption: user passes the appropriate command
    Basic error checking
'''
def execute_command(client,command):  
    
    try:
        stdin , stdout ,stderr =client.exec_command(command)        
        readBuffer = str(stdout.read(), encoding='utf-8')
        return readBuffer
    
    except Exception as inst:
        print ('\nCaught exception while executing command: {}\n'.format(command))
        return "NA"
        # print (type(inst))
        # print (inst.args)
        # print (inst)
		
'''	 
	Procedure to disconnect to remote host with given parameters and returning the shell handle
'''
def disconnect_host(client):
    client.close()

'''	 
	Procedure to execute command on given remote host 
	 and parse filed values and form a dictionary in basic.cfg
'''
def get_system_data(ip_address, username, password):
    try:
        if valid_ip(ip_address) is False:
            print('Invalid IP: {}'.format(ip_address))
            return None

        client = connect_host(ip1_list[i],uname_list[i],pword_list[i])
        if not client:
            return None

        system_data = dict()

        # Hostname
        hostname = execute_command(client, 'esxcli system hostname get')
        hostname = re.findall(r"Host Name:\s(\w+\d+)" , hostname)
        system_data['Hostname'] = hostname[0] if hostname and hostname[0] else 'NA'
        
        # hardware platform
        platform_details = execute_command(client, 'esxcli hardware platform get')
        platform = re.findall(r'Product Name:\s*(.*)',platform_details)
        vendor = re.findall(r'Vendor Name:\s*(.*)',platform_details)
        serial_no = re.findall(r'Serial Number:\s*(.*)',platform_details)
        system_data['Platform'] = platform[0] if platform and platform[0] else 'NA'
        system_data['Vendor'] = vendor[0] if vendor and vendor[0] else 'NA'
        system_data['Serial_Num'] = serial_no[0] if serial_no and serial_no[0] else 'NA'
        
        # System version
        system_version = execute_command(client, 'esxcli system version get')
        product = re.findall(r'Product:\s*(.*)',system_version)
        version = re.findall(r'Version:\s*(.*)',system_version)
        build = re.findall(r'Build:\s*(.*)',system_version)
        update = re.findall(r'Update:\s*(.*)',system_version)
        patch = re.findall(r'Patch:\s*(.*)',system_version)
        system_data['OS_Product'] = product[0] if product and product[0] else 'NA'
        system_data['Version'] = version[0] if version and version[0] else 'NA'
        system_data['Build'] = build[0] if build and build[0] else 'NA'
        system_data['Update'] = update[0] if update and update[0] else 'NA'
        system_data['Patch'] = patch[0] if patch and patch[0] else 'NA'
        
        # IP details
        ip_details = execute_command(client,'esxcli network ip interface ipv4 address list')
        my_reg= r"-\n(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)$"
        output = re.findall(my_reg,ip_details)
        name = output[0][0] if output and output[0] and output[0][0] else 'NA'
        ipaddr = output[0][1] if output and output[0] and output[0][1] else 'NA'
        netmask = output[0][2] if output and output[0] and output[0][2] else 'NA'
        broadcast = output[0][3] if output and output[0] and output[0][3] else 'NA'
        address_type = output[0][4] if output and output[0] and output[0][4] else 'NA'
        gateway = output[0][5] if output and output[0] and output[0][5] else 'NA'
        dhcp = output[0][6] if output and output[0] and output[0][6] else 'NA'
        
        system_data['Intf_Name'] = name
        system_data['IpV4_Addr'] = ipaddr
        system_data['Netmask'] = netmask
        system_data['Broadcast'] = broadcast
        system_data['Gateway'] = gateway
        system_data['Address_Type'] = address_type
        system_data['Dhcp'] = dhcp
        
        #DNS Details 
        dns_list = execute_command(client,'esxcli network ip dns server list')
        dns_list = re.search(r'DNSServers:\s*(.*)',dns_list)
        system_data['DNS_List'] = dns_list.group(1) if dns_list and dns_list.group(1) else 'NA'
        
        #Firmware Info
        AUL_Version = execute_command(client, 'cat /opt/ftsys/etc/ftSSS-release')        
        AUL_Version = re.search(r'([\w.-]+)',AUL_Version)
        system_data['AUL_Version'] = AUL_Version.group(1) if AUL_Version and AUL_Version.group(1) else 'NA'
        
        # system uuid
        uid = execute_command(client,'esxcli system uuid get')
        uuid = re.findall(r'([\w-]+)',uid)
        system_data['Uuid'] = uuid[0] if uuid and uuid[0] else 'NA'

        # hardware firmware type
        firmware = execute_command(client,'esxcli hardware firmwaretype get')
        firmware_type = re.findall(r'([\w]+)', firmware)
        system_data['Firmware_Type'] = firmware_type[0] if firmware_type and firmware_type[0] else 'NA'         
        client.close()
        return system_data
    except Exception as exp:
        print('\nCaught exception while collecting system data of: {}\n'.format(ip_address))
        # print(type(exp))
        # print(exp.args)
        # print(exp)

while True:

    switch_case = input("""
1. Add/Update Systems
2. Delete Systems
0. Exit
Enter a number: """)

    if isinstance(switch_case,str) and switch_case.isdigit():
        switch_case = int(switch_case)
    elif isinstance(switch_case, int):
        switch_case = switch_case
    else:
        print('invalid choice')
        break

    if switch_case == 0 :
        break

    elif switch_case == 1:
        print("Entered input is 1")
        print("Enter Systems details :")
        ip1_list = input("Enter IPs seperated by commas: ")
        uname_list = input("Enter Usernames seperated by commas: ")
        pword_list = input("Enter Passwords seperated by commas: ")
        ip1_list = [x.strip() for x in ip1_list.split(",")]
        uname_list = [x.strip() for x in uname_list.split(",")]
        pword_list = [x.strip() for x in pword_list.split(",")]
        
        new_systems_data = dict()

        if len(ip1_list) == len(uname_list) and len(ip1_list) == len(uname_list):
            for i in range(len(ip1_list)):
                system_data = get_system_data(ip1_list[i],uname_list[i],pword_list[i])
                if system_data:
                    new_systems_data[system_data['Hostname']] = system_data
                else:
                    print('Couldnt read data from {} with credentials {}/{}'.format(ip1_list[i],uname_list[i],pword_list[i]))
        else:
            print ("mismatch between entered inputs length")
            continue
        
        config_data = None
        if new_systems_data:
            if os.path.exists(config_file):
                with open(config_file, 'r') as file_handle:
                    try:
                        config_data = json.load(file_handle)
                    except ValueError as exp:
                        print('\nConfig file "{}" is corrupted\n'.format(config_file))
                        # print(type(exp))
                        # print(exp.args)
                        # print(exp)
                        config_data = None
                if not config_data:
                    print('Could not read file data!!!')
                    response = input('Do you want to overwrite the config file? [y|n]')
                    if response == 'n':
                        break
                    else:
                        config_data = dict()
            else:
                config_data = dict()

            for new_system in new_systems_data:
                config_data[new_system] = new_systems_data[new_system]

            with open(config_file, 'w') as file_handle:
                json.dump(config_data, file_handle, indent=4)
        else:
            print('No new data to write')

    elif switch_case == 2:
        
        config_data = None
        if os.path.exists(config_file):
            with open(config_file, 'r') as file_handle:
                try:
                    config_data = json.load(file_handle)
                except ValueError as exp:
                    print('\nConfig file "{}" is corrupted\n'.format(config_file))
                    # print(type(exp))
                    # print(exp.args)
                    # print(exp)
                    config_data = None
        else:
            print("\nCouldn't find any hosts to delete\n")
            continue
            
        current_hosts = config_data.keys()
        for index, host in enumerate(current_hosts):
            print("{}. {}".format(index, host))
        
        hostname = input("Please enter the hostname you want to delete")
        
        if hostname in config_data:
            confirm = input('Are you sure you want to delete system {} [y|n]'.format(hostname))
            if confirm == 'y':
                config_data.pop(hostname)
                print('\nDeleted the system "{}" successfully\n'.format(hostname))				
            else:
                print('Aborted deleting system {}'.format(hostname))
        else:  
	        print("Couldn't find the system with hostname: {}".format(hostname))
            
        with open(config_file, 'w') as file_handle:
            json.dump(config_data, file_handle, indent=4)         
        

    else:
        print("Invalid Choice")