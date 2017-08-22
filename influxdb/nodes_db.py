list_of_nodes = {} # virtual_id, gateway_ip, gateway_port

gateway_ip_temp_static = "192.168.1.100"

list_of_nodes['111'] =  {}
list_of_nodes['111']['gateway_ip'] = gateway_ip_temp_static
list_of_nodes['111']['gateway_port'] = 4000
list_of_nodes['111']['active'] = True

list_of_nodes['222'] =  {}
list_of_nodes['222']['gateway_ip'] = gateway_ip_temp_static
list_of_nodes['222']['gateway_port'] = 4001
list_of_nodes['222']['active'] = False

list_of_nodes['333'] =  {}
list_of_nodes['333']['gateway_ip'] = gateway_ip_temp_static
list_of_nodes['333']['gateway_port'] = 4002
list_of_nodes['333']['active'] = False