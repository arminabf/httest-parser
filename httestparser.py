import os
import argparse
from pyparsing import *

script = """
CLIENT
_${CONNECT} $HSP_FQDN $SEL_PORT
_${NEG}

_${REQ} GET /dynloc?0x5cr0x5cn
__Host: DynamicHost
__User-Agent: curl
__
_${SUBMIT}
_${WAIT}
_CLOSE
END

CLIENT
_SECOND
END

SERVER
_RES
_WAIT
__HTTP/1.1 200 Ok
__foo:bar
__
__param
END

SERVER SSL:$HGW_AS1_PORT
_RES
_WAIT
__HTTP/1.1 200 Ok
__Content-Length: AUTO
__Content-Type: text/plain
__
__==AS1-OK==
_CLOSE
END
"""

def parse_arguments():
	""" Creates the argument parser and parses the arguments.
	:returns: The arguments returned from the parser.
	"""
	script = os.path.relpath(__file__)
	description = "TODO"
	parser = argparse.ArgumentParser(description=description,
	                                 formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("--verbose", help="verbose output",
	                    action="store_true")
	parser.add_argument("script", help="Script file to be parsed")

	return parser.parse_args()

# common literals
lit_alphanum = Word(alphanums)
lit_num = Word(nums)
lit_printables = Word(printables)
lit_hdr = Word(printables, excludeChars=":")
lit_body = Word(printables)
lit_var = Word(alphanums)("env-var")
lit_expect_hdrs = CaselessKeyword("headers")
lit_expect_body = CaselessKeyword("body")
lit_expect_exec = CaselessKeyword("exec")
lit_prot_h1 = Literal("HTTP/1.1")

# command literals
block_end = Literal("END").suppress()

cmd_res = Literal("_RES")
cmd_req = Literal("_REQ")
cmd_req_uni = Literal("_${REQ}")
cmd_wait = Literal("_WAIT")
cmd_data = Literal("__").suppress()
cmd_close = Literal("_CLOSE")
cmd_expect = Literal("_EXPECT")
cmd_match = Literal("_MATCH")

expect_match_type = lit_expect_hdrs | lit_expect_body("type")
expect = Group(cmd_expect + \
			   expect_match_type + \
			   QuotedString("\"")("regex"))
match = Group(cmd_match + \
			  expect_match_type + \
			  QuotedString("\"")("regex") + \
			  lit_var)

# compounds
header = lit_hdr("name") + ":" + lit_hdr("value")
headerline = Group(cmd_data + header)
headers = Group(ZeroOrMore(headerline))("headers")

statuscode = Word(nums, max=3)("statuscode")
statusphrase = Word(alphas)("statusphrase")
statusline = Group(cmd_data + lit_prot_h1.suppress() + statuscode + statusphrase)("statusline")

bodyline = Group(cmd_data + lit_body)
body = Group(ZeroOrMore(bodyline))("body")

#
# blocks
#

# SERVER
global_server = Literal("SERVER") + \
					Optional(Literal("SSL")("ssl") + ":") + \
					Word(alphanums + "$" + "_")("port")
block_response = Group(cmd_res + \
					   ZeroOrMore(expect)("expectations") + \
					   ZeroOrMore(match)("matches") + \
					   cmd_wait + \
					   statusline + \
					   headers + \
					   cmd_data + \
					   body + \
					   Optional(cmd_close))
body_server = Group(ZeroOrMore(block_response))("response")
block_server = global_server + body_server + block_end

# CLIENT
global_client = Literal("CLIENT") + Optional(lit_num)("number")
block_request = Group(cmd_req_uni + \
					   ZeroOrMore(expect)("expectations") + \
					   ZeroOrMore(match)("matches") + \
					   cmd_wait + \
					   statusline + \
					   headers + \
					   cmd_data + \
					   body + \
					   Optional(cmd_close))
body_client = Group(ZeroOrMore(block_request))("request")

block_client = global_client.setDebug() + block_end

def main():
	args = parse_arguments()
	with open(args.script, 'r') as f:
		servers = block_server.searchString(f.read())
		#print(servers.dump())
		clients = block_client.searchString(f.read())
		print(clients.dump())
	#for server in serverblocks.asList():
	    #responseblocks = responseblock.searchString(server)
        #print(responseblock.dump())
		#print(server)
 
if __name__ == "__main__":
    main()
