#!/usr/bin/python3

import argparse
import json
import pprint
import subprocess
import sys





CEPH_BIN = '/usr/bin/ceph'


def _exec(args):
	cmd  = subprocess.Popen(args,
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
	result = b''.join(cmd.stdout.readlines()).decode('utf8')
	if result == []:
		error = cmd.stderr.readlines()
		exit( "ERROR: %s" % error  )
	return result	

def _getNodeById(lNodeList,iId):
	for dNode in lNodeList:
#		pprint.pprint([dNode['id'],iId])
		if dNode['id'] == iId:
			return dNode
	return

#stype sind osd host etc
def _getNodesByType(lNodeList,sType):
	retval = []
	for dNode in lNodeList:
		if dNode['type'] == sType:
			retval.append(dNode)
	return retval



def _cephGetTree():
	tree_json = _exec([CEPH_BIN,'osd','tree','-f','json'])	
	tree = json.loads(tree_json)
	return tree


def main(sJson):
    j = json.loads(sJson)
    #pprint.pprint(j)

    channels = []
    e = 0
    h = { 
        'HEALTH_OK' : 0, 'HEALTH_WARN' : 1, 'HEALTH_ERR' : 2 
    }[ j['health']['status'] ]
    e = max(e,h)
    channels.append( { 
        'channel' : 'status', 
        'value' : h
    } )

    i = j['osdmap']['osdmap']['num_osds'] / j['osdmap']['osdmap']['num_up_osds']
    channels.append( {
        'channel' : 'osds_up',
        'value' : i
    } )

    print( json.dumps({
        'error' : e,
        'result' : channels
    }) )
    
    return






argparserbase = argparse.ArgumentParser()
argparserbase.add_argument("--json-file", help="a file to parse instead of reading `ceph -s`")
args = argparserbase.parse_args()

if (args.json_file):
    with open(args.json_file,'r', encoding="utf8") as file: sJson = file.read()
else:
    sJson = _exec([CEPH_BIN,'-s','--format=json'])

main(sJson)


#_exec([CEPH_BIN,'osd','crush','remove',dOsd['name']])



