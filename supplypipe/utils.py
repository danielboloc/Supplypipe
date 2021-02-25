import re

def str2list(string):
	# remove multiple whitespaces to just leave one
	return string.replace(",", " ").split()

def list2str(l):
	return " ".join(" ".join(l).replace(",", " ").split())