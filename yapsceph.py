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


argparserbase = argparse.ArgumentParser(add_help=False)
argparserbase.add_argument("objtype", choices=['osd'],help="which object-type to work on")

class NoArgs:
	def args(self):
		argparser = argparse.ArgumentParser(parents=[argparserbase])
		argparser.add_argument("objtype", choices=['osd'],help="which object-type to work on")
		return argparser

	def run(self):
		args = self.args().parse_args()
		print( 'no args - doing nothing')

class yapsOsd:
	def args(self):
		argparser = argparse.ArgumentParser(parents=[argparserbase])
		argparser.add_argument("method",choices=['rm','dump','create_withlog'],help="which method to use")
		argparser.add_argument("--osd",  type=int, help="which osd to work on")

		return argparser
	
	def run(self):
		args = self.args().parse_args()
#		pprint.pprint(args)
		if args.method == "rm":
			self.rm(args)

		if args.method == "dump":
			self.dump()

	def dump(self):
		tree_json = _exec([CEPH_BIN,'osd','tree','-f','json-pretty'])
		print(tree_json)
		

	# this is an implementation to remove osd
	def rm(self,args):
		if "" == str(args.osd):
			sys.exit("no --osd given")
		tree = _cephGetTree()
#		pprint.pprint(tree['nodes'])
		dOsd = _getNodeById(tree['nodes'],args.osd)
		if not dOsd:
			exit("osd %s not found" % args.osd  )
		dlHosts = _getNodesByType(tree['nodes'],'host')
#		pprint.pprint(dlHosts);
		if not dlHosts or len(dlHosts) == 0:
			exit("no hosts at all")

		dHost = None
		for h in dlHosts:
			if dOsd['id'] in h['children']:
				dHost = h
				break
		if not dHost:
			exit("host not found for osd id {}".format(dOsd['id']))

		print( "about to remove osd {} from host {} ".format(dOsd['name'],dHost['name']) )
			
		_exec([CEPH_BIN,'osd','out',str(dOsd['id'])])
		out = _exec(['/usr/bin/ssh',dHost['name'],
			'sudo systemctl stop ceph-osd@{0}.service 2>&1 && sudo umount /var/lib/ceph/osd/ceph-{0} 2>&1 && echo ok'.format(dOsd['id'])
			]);
		if out != "ok\n" :
			exit("error on stopping {}: '{}'".format(dOsd['name'],out))
		_exec([CEPH_BIN,'osd','crush','remove',dOsd['name']])
		_exec([CEPH_BIN,'auth','del',dOsd['name']])
		_exec([CEPH_BIN,'osd','rm',str(dOsd['id'])])


#out = _exec(['/usr/bin/ssh','kbbceph04','sudo ls -l /root 2>&1 && ls -l /root 2>&1 && echo ok'])
#exit("ok:"+out+'sdf')

# this phrase is lame, but ...
if sys.argv[1] == 'osd':
	op = yapsOsd()
else:
	op = NoArgs()

op.run()

#pprint.pprint(args)





exit()
