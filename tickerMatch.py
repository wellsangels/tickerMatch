#!/usr/bin/python
# -*- coding: utf-8 -*-

import unicodedata
import string
import collections
import csv
import os.path
import distance
import re

# a dictionary for adding known abbreviations for big companies that are frequently used
known_abbrevs = {"fannie mae":"FNMA","ibm":"IBM","freddie mac":"FMCC","ups":"UPS","aig":"AIG","adp":"ADP"}
# a list of common words that are better off deleted
delete_words = ['inc','corporation','corp','adr','ltd','sponsored','company','holdings','co','incorporated','partners','limited','sa','holding','properties','group','industries','technologies','plc','com','lp', 'class', 'a', 'b', 'c', 'the', 'of']

#main function 
def ticker_match(search_file = None, lookup_file = None): 
	if lookup_file is None: 
		lookup_file = "tickerMatchLookup.csv"
	if search_file is None: 
		search_file = "tickerSearch.csv"
	lookup_dictionary = create_lookup_dictionary(lookup_file)
	search_list = create_results_dictionary(search_file)
	search_list = find_exact_matches(search_list, lookup_dictionary)
	search_list = check_known_abbrevs(search_list, known_abbrevs)
	search_list = find_fuzzy_matches(search_list, lookup_dictionary)
	output_file(search_list)

######LOAD/OUTPUT FUNCTIONS######
#look for file, return the reader object
def load_file(file_name):
	if os.path.isfile(file_name): 
		f = open(file_name,"rU")
		reader = csv.reader(f)
		return reader
	else: 
		print("File not found.")
		exit()

#output file from search list
def output_file(search_list): 
	f = open("tickerMatchResults.csv","w")
	writer = csv.writer(f)
	writer.writerows(search_list)
	f.close()

######DATA STORAGE FUNCTIONS######
#used to find the common words in the names of all companies
def find_common_words(lookup_dictionary):
	combined_token_names = []
	for key, val in lookup_dictionary.items(): 
		combined_token_names.extend(tokenize_name(key))
	counter = (collections.Counter(combined_token_names))
	most_common_words = counter.most_common(10)
	#get the sum of all words
	top_words = max(counter.values())
	#create a frequency dictionary
	frequency_dic = dict()
	#invert frequency so that the least common are more powerful
	for word in most_common_words: 
		frequency_dic[word[0]] = (top_words-word[1])/top_words
	return frequency_dic

# takes a csv file structured with TICKER, NAME and creates a dictionary with CLEANED NAME as key and TICKER AND NAME as array
def create_lookup_dictionary(lookup_file):
	reader = load_file(lookup_file)
	lookup_dictionary = dict()
	for line in reader: 
		ticker = line[0]
		dirty_name = line[1]
		clean_name = name_cleaner(dirty_name)
		lookup_dictionary[clean_name] = [dirty_name, ticker]
	return lookup_dictionary

# takes a csv file with just UNCLEANED NAMES, creates list of lists with UNCLEANED NAMES and CLEANED NAMES
def create_results_dictionary(search_file): 
	reader = load_file(search_file)
	search_list = []
	for line in reader: 
		dirty_name = line[0]
		clean_name = name_cleaner(dirty_name)
		search_list.append([dirty_name,clean_name])
	return search_list

######SPECIFIC CLEAN AND MEASURING FUNCTIONS######

# measure the frequency-adjusted similarity of two search strings
def distance_measure(search_string, key_string, frequency_dic): 
	search_string_words = search_string.split()
	key_string_words = key_string.split()
	total_score = 0
	for word in search_string_words: 
		if word in key_string_words: 
			if word in frequency_dic.keys(): 
				total_score = frequency_dic[word]+total_score	
			else: 
				total_score = 1 + total_score
		else: 
			if word in frequency_dic.keys(): 
				total_score = total_score - frequency_dic[word]	
			else: 
				total_score = total_score - 1
	# if total_score <= 0: 
	# 	jaccard_score = distance.jaccard(search_string, key_string)
	# 	if jaccard_score < 0.0001: 
	# 		total_score = 0.001

	return total_score

# function for converting sloppy company names to cleaned names
def name_cleaner(unclean_company): 
	#convert to lower
	clean_company = unclean_company.lower()
	#remove all punctuation 
	clean_company = re.sub('['+string.punctuation+']', '', clean_company)
	#transliterate any unicode to ascii
	''.join(x for x in unicodedata.normalize('NFKD', str(clean_company)) if x in string.ascii_letters).lower()
	#remove these common words from company names (also removes extra spaces)
	clean_company = [' '.join(w for w in clean_company.split() if w not in delete_words)]
	return clean_company[0]

#simple tokenize
def tokenize_name(name):
	return name.split()

######MATCHING FUNCTIONS######
# find companies with exact matches and add to search list
def find_exact_matches(search_list, lookup_dictionary): 
	for search_item in search_list: 
		if search_item[1] in lookup_dictionary.keys(): 
			for term in lookup_dictionary[search_item[1]]:
				search_item.append(term)
			search_item.append("")
	return search_list

#function to go through the known abbreviation list and add to the search list
def check_known_abbrevs(search_list, known_abbrevs): 
	for search_item in search_list: 
		if search_item[1] in known_abbrevs.keys(): 
			search_item.append(search_item[1])
			search_item.append(known_abbrevs[search_item[1]])
			search_item.append("abbrev")
	return search_list

# if no exact match, find fuzzy matches
def find_fuzzy_matches(search_list, lookup_dictionary): 
	frequency_dic = find_common_words(lookup_dictionary)
	for search_item in search_list: 
		if len(search_item) < 3: 
			max_match = 0
			final_key = ""
			for key, val in lookup_dictionary.items(): 
				this_match = distance_measure(search_item[1], key, frequency_dic)
				# (this_match_letters+this_match_words)/2
				if this_match > max_match: 
					final_key = key
					max_match = this_match
			if final_key == "": 
				search_item.append("")
				search_item.append("")
				search_item.append("NONE FOUND")
			else: 
				search_item.append(lookup_dictionary[final_key][0])
				search_item.append(lookup_dictionary[final_key][1])
				search_item.append("guess")
	return search_list

# call main function 
if __name__=="__main__":
	ticker_match()
