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

def assemble_func(keyword):
	return Combine(Literal("_") + \
			Literal("$") + \
			Optional("{") + \
			Literal(keyword) + \
			Optional("}"))

#
# common literals
#
lit_prot_h1 = Literal("HTTP/1.1")
lit_data = Literal("__").suppress()
lit_data_nocr = Literal("_-").suppress()

#
# commond words
#
word_alphanum = Word(alphanums)
word_num = Word(nums)
word_printables = Word(printables)
word_hdrname = Word(printables, excludeChars=":")
word_hdrvalue = Word(printables + ' ')
word_data = Word(printables)
word_variable = Word(alphanums + "_")
word_env_variable = Combine("$" + \
					Optional("{") + \
					word_variable + \
					Optional("}"))
word_param = word_printables | word_env_variable

#
# common keywords
#
key_expect_hdrs = CaselessKeyword("headers")
key_expect_body = CaselessKeyword("body")
key_expect_exec = CaselessKeyword("exec")
key_expect_dot = CaselessKeyword(".")

#
# global and command keywords
#
block_end = Keyword("END").suppress()
cmd_res = Keyword("_RES")
cmd_req = Keyword("_REQ")
cmd_wait = Keyword("_WAIT")
cmd_close = Keyword("_CLOSE")
cmd_expect = Keyword("_EXPECT")
cmd_match = Keyword("_MATCH")
cmd_hdr_body_sep = Keyword("__")

#
# custom commands
#
cmd_expect_h1 = Keyword("_EXPECT_H1_ONLY")
cmd_expect_h2 = Keyword("_EXPECT_H2_ONLY")

#
# custom functions
#
func_connect = assemble_func("CONNECT")
func_neg = assemble_func("NEG")
func_req = assemble_func("REQ")
func_expect_status = assemble_func("EXPECT_STATUS")
func_submit = assemble_func("SUBMIT")
func_wait = assemble_func("WAIT")

#
# common compounds
#
comment = '#' + restOfLine
expect_match_type = key_expect_hdrs | \
					key_expect_body | \
					key_expect_exec | \
					key_expect_dot
expect = Group((cmd_expect | cmd_expect_h1 | cmd_expect_h2) + \
			   expect_match_type("type") + \
			   QuotedString("\"")("regex")) | \
         Group(func_expect_status + word_num("status"))

match = Group(cmd_match + \
			  expect_match_type("type") + \
			  QuotedString("\"")("regex") + \
			  word_variable("variable"))

header = word_hdrname("name") + ":" + word_hdrvalue("value")
headerline = Group(lit_data + header)
headers = Group(ZeroOrMore(headerline))("headers")

statuscode = Word(nums, max=3)("statuscode")
statusphrase = Word(alphas)("statusphrase")
statusline = Group(lit_data + lit_prot_h1.suppress() + statuscode + statusphrase)("statusline")

bodyline = Group(lit_data + word_data)
body = Group(ZeroOrMore(bodyline))("body")

#
# SERVER compounds
#
global_server = Literal("SERVER") + \
					Optional(Literal("SSL")("ssl") + ":") + \
					Word(alphanums + "$" + "_")("port")
block_response = Group(cmd_res + \
					   ZeroOrMore(expect)("expectations") + \
					   ZeroOrMore(match)("matches") + \
					   cmd_wait + \
					   statusline + \
					   headers + \
					   cmd_hdr_body_sep + \
					   Optional(body) + \
					   Optional(cmd_close))
body_server = Group(ZeroOrMore(block_response))("response")
block_server = global_server + body_server + block_end

#
# CLIENT compounds
#
global_client = Literal("CLIENT") + Optional(word_num)("procs")

connection = (func_connect | cmd_req) + \
				word_param("host") + \
				Optional("SSL:") + \
				word_param("port") + Optional(func_neg)
request = func_req + \
		   word_param("method") + \
		   word_param("path")
block_request = Group(request + \
					  headers + \
					  cmd_hdr_body_sep + \
					  Optional(body) + \
					  ZeroOrMore(expect)("expectations") + \
					  ZeroOrMore(match)("matches") + \
					  (cmd_wait | (func_submit + func_wait)) + \
					  Optional(cmd_close)
					 )
requests = Group(connection("connection") + ZeroOrMore(block_request)("requests"))

body_client = ZeroOrMore(requests)("fuck")
block_client = global_client + body_client + block_end
block_client.ignore(comment)

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
