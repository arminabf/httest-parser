import os
import argparse
from pyparsing import *

def parse_arguments():
	""" Creates the argument parser and parses the arguments.
	:returns: The arguments returned from the parser.
	"""
	description = "TODO"
	parser = argparse.ArgumentParser(description=description,
	                                 formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("--verbose", help="verbose output",
	                    action="store_true")
	parser.add_argument("script", help="Script file to be parsed")

	return parser.parse_args()

# common literals
lit_prot_h1 = Literal("HTTP/1.1")

# commond words
word_alphanum = Word(alphanums)
word_num = Word(nums)
word_printables = Word(printables)
word_hdr_nv = Word(printables, excludeChars=":")
word_data = Word(printables)
word_variable = Word(alphanums + "_")
word_env_variable = Combine("$" + \
					Optional(Literal("{")) + \
					word_variable + \
					Optional(Literal("}")))
word_param = word_printables | word_env_variable

# common keywords
key_expect_hdrs = CaselessKeyword("headers")
key_expect_body = CaselessKeyword("body")
key_expect_exec = CaselessKeyword("exec")

# global and command literals
block_end = Literal("END").suppress()
cmd_res = Literal("_RES")
cmd_req = Literal("_REQ")
cmd_req_uni = Literal("_${REQ}")
cmd_wait = Literal("_WAIT")
cmd_data = Literal("__").suppress()
cmd_data_nocr = Literal("_-").suppress()
cmd_close = Literal("_CLOSE")
cmd_expect = Literal("_EXPECT")
cmd_match = Literal("_MATCH")

def assemble_func(keyword):
	return Combine(Literal("_") + \
			Literal("$") + \
			Optional(Literal("{")) + \
			Literal(keyword) + \
			Optional(Literal("}")))

func_connect = assemble_func("CONNECT")
func_neg = assemble_func("NEG")
func_req = assemble_func("REQ")

expect_match_type = key_expect_hdrs | key_expect_body("type")
expect = Group(cmd_expect + \
			   expect_match_type + \
			   QuotedString("\"")("regex"))
match = Group(cmd_match + \
			  expect_match_type + \
			  QuotedString("\"")("regex") + \
			  word_variable)

# compounds
header = word_hdr_nv("name") + ":" + word_hdr_nv("value")
headerline = Group(cmd_data + header)
headers = Group(ZeroOrMore(headerline))("headers")

statuscode = Word(nums, max=3)("statuscode")
statusphrase = Word(alphas)("statusphrase")
statusline = Group(cmd_data + lit_prot_h1.suppress() + statuscode + statusphrase)("statusline")

bodyline = Group(cmd_data + word_data)
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
global_client = Literal("CLIENT") + Optional(word_num)("number")

connection = (func_connect | cmd_req) + \
				word_param("host") + \
				Optional("SSL:") + \
				word_param("port") + Optional(func_neg)
request = Group(func_req + \
				word_param("verb") + \
				word_param("url"))("request")
block_request = Optional(connection) + \
					request + \
					headers + \
					cmd_data + \
					body
					   # ZeroOrMore(expect)("expectations") + \
					   # ZeroOrMore(match)("matches") + \
					   # cmd_wait + \
					   # statusline + \
					   # headers + \
					   # cmd_data + \
					   # body + \
					   # Optional(cmd_close)
					  #)
body_client = Group(ZeroOrMore(block_request))("request")

block_client = global_client + block_request + block_end

def main():
	args = parse_arguments()
	with open(args.script, 'r') as f:
		servers = block_server.searchString(f.read())
		print(servers.dump())
	with open(args.script, 'r') as f:
		clients = block_client.searchString(f.read())
		print(clients.dump())
	#for server in serverblocks.asList():
	    #responseblocks = responseblock.searchString(server)
        #print(responseblock.dump())
		#print(server)
 
if __name__ == "__main__":
    main()
