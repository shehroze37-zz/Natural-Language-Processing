import os
import imp
import math
import collections
import operator
import sys

def writeLineToFile(newFile,newLine,sentences):

	#this function writes a cleaned line to a file
	if newLine != "" and newLine != '\n':
		sentences.append(newLine)
		newFile.write(newLine.strip())
		newFile.write("\n")
		return 1
	else:
		return 0	

def findRareWords(word_tag_occurences, rare_list):

	#if a word has less that 4 occurences then we treat it as a rare word, In this method we dont do anything with the word but just store the tag of
	#rare words along with the frequency
	for key,value in word_tag_occurences.iteritems():
		if word_tag_occurences[key] <= 4:
			#print("adding to rare " + key)
			string_parts = key.split("/")

			if len(string_parts) < 2:
				print("Error in finding rare words with key : " + key)
				exit()

			if string_parts[1] in rare_list:
				rare_list[string_parts[1]] = rare_list[string_parts[1]] + value
			else:
				rare_list[string_parts[1]] = 1

def countOccurences(line, word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences, trigram_occurences):
	

	#This method counts occurences for words, tags, words|tags, bigrams and trigrams

	if line == "\n":
		return
	elif line == "":
		return	

	#do the words need to be converted to lower case ?????	
	puncuations = [".", ":", ",", "``", "(", "", " "]

	word_tags = line.split(" ")
	previous_previous_tag = "**start**"
	previous_tag = "**start**"

	start_tag = "**start**"
	end_tag = "**end**"

	if start_tag in tag_occurences:
		tag_occurences[start_tag] = tag_occurences[start_tag] + 1
	else:
		tag_occurences[start_tag] = 1	

	for word_tag in word_tags:

		word_parts = word_tag.split("/")
		newList = word_parts[0:int(len(word_parts) - 1)]
		new_word = "".join(newList)

		word_parts[len(word_parts) - 1] = word_parts[len(word_parts) - 1].replace("\n", "")

		if word_parts[len(word_parts) - 1] in puncuations :
			continue

		if word_tag == "":
			continue 

		if new_word in word_occurences:
			word_occurences[new_word] = word_occurences[new_word] + 1
		else:
			word_occurences[new_word] = 1	

		tag = word_parts[len(word_parts) - 1]

		new_word_tag = new_word + "/" + tag	
			
		if new_word_tag in word_tag_occurences:
			word_tag_occurences[new_word_tag] = word_tag_occurences[new_word_tag] + 1
		else:
			word_tag_occurences[new_word_tag] = 1	

		
		if tag in tag_occurences:
			tag_occurences[tag] = tag_occurences[tag] + 1
		else:
			tag_occurences[tag] = 1 

		next_tag = previous_tag + "/" + tag
		if next_tag in tag_next_tag_occurences:
			tag_next_tag_occurences[next_tag] = tag_next_tag_occurences[next_tag] + 1
		else:
			tag_next_tag_occurences[next_tag] = 1

		trigram_tag = previous_previous_tag + "/" + previous_tag + "/" + tag
		if trigram_tag in trigram_occurences:
			trigram_occurences[trigram_tag] = trigram_occurences[trigram_tag] + 1
		else:
			trigram_occurences[trigram_tag] = 1

		previous_previous_tag = previous_tag	
		previous_tag = word_parts[len(word_parts) - 1]

	last_tag_finish_tag = previous_tag + "/" + end_tag
	if last_tag_finish_tag in tag_next_tag_occurences:
		tag_next_tag_occurences[last_tag_finish_tag] = tag_next_tag_occurences[last_tag_finish_tag] + 1
	else:
		tag_next_tag_occurences[last_tag_finish_tag] = 1				

def calculateProbabilities(word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences, probability_tag, probability_word_tag):
	
	#this function calculates the emission and transition probabilities from the training
	#THese probabilities are used to create the HMM

	roundOff = 5 
	V = len(tag_occurences)	

	for key,value in word_tag_occurences.iteritems():
		string_parts = key.split("/")
		probability = round((value + 1) / float(tag_occurences[string_parts[1]] + V),roundOff)
		#probability = round((value ) / float(tag_occurences[string_parts[1]] ),roundOff)
		probability_word_tag[key] = probability
		if(probability > 1):
			print("ERROR : Probability P(Word = " + string_parts[0] + "| Cat = "+string_parts[1] +" ) = " + `probability`)
			exit()

	V = len(tag_occurences)	

	for key,value in tag_next_tag_occurences.iteritems():
		string_parts = key.split("/")
		new_key_probability = string_parts[1] + "/" + string_parts[0]
		probability = round((value + 1) / float(tag_occurences[string_parts[0]] + V),roundOff)
		#probability = round((value ) / float(tag_occurences[string_parts[0]] ),roundOff)
		probability_tag[new_key_probability] = probability
		if(probability > 1):
			print("ERROR : Probability P(Tag n+1 = " + string_parts[1] + "| Tag n = " + string_parts[0] +" ) = " + `probability`)
			exit()	

def getTagsForIndexes(tag_list, indices):
	output = []
	previous_key = 0
	count = 0
	for key,value in indices.iteritems():		
		if count != 0:
			if key > previous_key:
				print("Error : ")
				exit()
		output.append(tag_list[value])		
		count += 1		
		previous_key = key 
	return output[::-1]					

def viterbi(sentence, word_occurences, tag_occurences,word_tag_occurences, tag_next_tag_occurences, probability_tag, probability_word_tag, rare_list, trigram):
	
	#This is where all the magic happens

	N = 0 
	words = sentence.split(" ")
	for word in words:
		if word != " " and word != "\n" and word != "":
			N += 1

	score = {}
	backpointer = {}
	V = len(tag_occurences)	

	tag_list = list(tag_occurences.keys())
	K = len(tag_occurences.keys())
	for i in range(0,K):
		#treat unobserved biagrams if they have alrady been seen once 
		wordFound = word_occurences.get(words[0])
		result = 0

		probability_tag_i_given_start = 0
		if probability_tag.get(tag_list[i] + "/**start**") != None:
			probability_tag_i_given_start = probability_tag[tag_list[i] + "/**start**"]
		else:
			probability_tag_i_given_start = float(1) / float(tag_occurences["**start**"])	

 		probability_first_word_given_tag_i = 0.0000000001
		

		#If a word is not found then we calculate the probability using the tags from our rare list
		if wordFound == None:
			if tag_list[i] in rare_list:
				probability_first_word_given_tag_i = float(rare_list[tag_list[i]]) / float(tag_occurences[tag_list[i]])	
		else:
			word_tag_biagram = probability_word_tag.get(words[0] + "/" + tag_list[i])
			if word_tag_biagram == None:
				probability_first_word_given_tag_i = 0.0000000001
			else:
				probability_first_word_given_tag_i = probability_word_tag[words[0] + "/" + tag_list[i]]
		
		result = probability_first_word_given_tag_i * probability_tag_i_given_start	

		#We need to make sure that the probability is not zero just to make better predictions	
		if result == 0 : 
			print("Error : Underflow")
			exit()	

		score[i,0] = result
		backpointer[i,0] = 0

	for j in range(1,N):

		word_j = words[j]
		for i in range(0,K):
			maximumScore = 0
			maxK = 0
			tag_i = tag_list[i]
			y_2 = '**start**'

			for k in range(0,K):
				
				tag_k = tag_list[k]
				probability_tagi_given_tagk = 0.0000000001
				countOfTagK = tag_occurences[tag_k]

				#calculating the transition probability for our bigram
				if tag_next_tag_occurences.get(tag_k + "/" + tag_i) == None:
					#probability_tagi_given_tagk = 1 / float(countOfTagK)	
					probability_tagi_given_tagk = 0.0000000001	
				else:
					if probability_tag.get(tag_i + "/" + tag_k) == None :
						#probability_tagi_given_tagk = (tag_next_tag_occurences.get(tag_k + "/" + tag_i) ) / float(countOfTagK )
						probability_tagi_given_tagk = 0.0000000001
					else:
						probability_tagi_given_tagk = probability_tag[tag_i + "/" + tag_k]

				#trying the trigrams
				'''if trigram.get( y_2 +"/" + tag_k + "/" + tag_i) != None and tag_next_tag_occurences.get(tag_k + "/" + tag_i) != None:
					probability_tagi_given_tagk = float(trigram[ y_2 +"/" + tag_k + "/" + tag_i]) / float(tag_next_tag_occurences[tag_k + "/" + tag_i])'''		
				
				#calculating emission probability
				probability_wordj_given_tagi = 0
				if word_occurences.get(word_j) == None:
					
					if tag_i in rare_list:
						probability_wordj_given_tagi = float(rare_list[tag_i]) / float(tag_occurences[tag_i])
					
				else:
					word_tag_biagram = probability_word_tag.get(word_j + "/" + tag_i)
					if word_tag_biagram == None:
						probability_wordj_given_tagi = 0
					else:
						probability_wordj_given_tagi = probability_word_tag[word_j + "/" + tag_i]


				if probability_wordj_given_tagi > 1 or probability_wordj_given_tagi < 0 or probability_tagi_given_tagk > 1 or probability_tagi_given_tagk < 0:
					print("Wrong Probability => P(word|tag) = " + `probability_wordj_given_tagi` + " and transition = " + `probability_tagi_given_tagk`)
					exit()

				if k == 1:
					maximumScore = score[k,j - 1] * probability_tagi_given_tagk * probability_wordj_given_tagi
					maxK = k
				else:
					calculated_score = score[k,j - 1] * probability_tagi_given_tagk * probability_wordj_given_tagi
					if calculated_score > maximumScore : 
						maximumScore = calculated_score
						maxK = k 
						
			score[i,j] = maximumScore
			backpointer[i,j] = maxK
			y_2 = tag_list[maxK]


	#We just get the backpointer to get the tags from our predictions
	setOfOutputTags = collections.OrderedDict()
	currentScore = score[0,N - 1]
	setOfOutputTags[N - 1] = 0
	for i in range(1,K):
		if score[i,N - 1 ] > currentScore:
			currentScore = score[i,N - 1 ]
			setOfOutputTags[N - 1] = i

	for j in range(N - 2, -1, -1):
		setOfOutputTags[j] = backpointer[setOfOutputTags[j+1], j+1]	
	return getTagsForIndexes(tag_list,setOfOutputTags)	


def cleanFile(word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences,trigram_occurences, frequency_sentences,sentences):

	#THis method just cleans the files and adds the new sentences to new files, it also calculates the occurences of words and tags from the 100% data

	totalSentences = 0
	removeChars = ["[", "]","]\n","-/:", "''/''", "''/''\n", ",/,", ")/)", "(/(", "{/(", "}/)", ":/:", "`/``", "'/''", "``/``", "``/``\n", "--/:", " ", "\n", "\r\n"]
	debug = False 
	for subdir, dirs, files in os.walk("WSJ-2-12"):
		for fn in files:
			subpaths = subdir.split("/")
			filepath = subpaths[1] + "/" + fn
			if not os.path.exists("new-tags/" + subpaths[1]):
				os.makedirs("new-tags/" + subpaths[1])
			if filepath.endswith(".POS"):

				sentencesInFile = 0

				print (subdir + "/" + fn)
				fileNameParts = fn.split(".")
				newFile = open("new-tags/" + subpaths[1] + "/" + fileNameParts[0] + ".txt", "wb")
				newLine = ""

				if fileNameParts[0] == "WSJ_1000" :
					debug = False
				else:
					debug = False	

				with open(subdir + "/" + fn, "r") as readFile:
					
					for line in readFile:
						if debug == True:
							print("Reading Line : " + line)
						if not line in removeChars:
							lineParts = line.split(" ")
							if "=====" in lineParts[0]:
								if not newLine in removeChars:	
									if(debug == True):
										print("adding line " + newLine)

									sentencesInFile  = sentencesInFile + writeLineToFile(newFile, newLine,sentences)
									countOccurences(newLine, word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences,trigram_occurences)
								newLine = ""
							else:
								for stParts in lineParts :
									if not stParts in removeChars :
										if stParts == "./.":
											sentencesInFile  = sentencesInFile + writeLineToFile(newFile, newLine,sentences)
											countOccurences(newLine, word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences, trigram_occurences)
											newLine = ""
										elif stParts != "``/``":
											newLine = newLine + " " + stParts

				if newLine != "":
					if not newLine in removeChars:
						if(debug == True):
							print("adding line finally " + newLine)
						sentencesInFile  = sentencesInFile + writeLineToFile(newFile, newLine,sentences)
						countOccurences(newLine, word_occurences, tag_occurences, word_tag_occurences, tag_next_tag_occurences, trigram_occurences)
						newLine = ""

				totalSentences = totalSentences + sentencesInFile
				frequency_sentences[subpaths[1] + "/" + fileNameParts[0]] = sentencesInFile
				sentencesInFile = 0
				newFile.close() 
	return totalSentences

def removeTags(line):

	#Helper function to remove the tags from a cleaned line and returns the line
	newLine = ""
	lineParts = line.split(" ")
	for part in lineParts:
		word_tag_part = part.split("/")
		newList = word_tag_part[0:int(len(word_tag_part) - 1)]
		new_word = "".join(newList)
		if word_tag_part[0] != " " and word_tag_part[0] != "" and new_word != "" and new_word != " ":
			newLine += new_word + " "
	return newLine	

def getTags(line) :

	#Helper function to get the tags of a cleaned sentence
	tags = []
	lineParts = line.split(" ")

	for part in lineParts:
		word_parts = part.split("/")
		newList = word_parts[0:int(len(word_parts) - 1)]
		new_word = "".join(newList)
		if word_parts[0] != " " and word_parts[0] != "" and word_parts[len(word_parts) - 1] != " " and word_parts[len(word_parts) - 1] != "":
			tag = word_parts[len(word_parts) - 1].replace("\n", "")
			tags.append(tag)
	return tags	


def calculateAccuracy(original_tags,predicted_tags):
	#THis helper function calculates the accuracy using the set of original tags and predicted tags
	if len(original_tags) != len(predicted_tags):
		print(original_tags)
		return -1	
	else:
		correct = 0
		for first_tag,second_tag in zip(original_tags,predicted_tags):
			if first_tag == second_tag:
				correct += 1
		return round(correct / float(len(original_tags)),5)	* 100

def cleanList(word_occurences_90, tag_occurences_90, word_tag_occurences_90, tag_next_tag_occurences_90, probability_tag_90, probability_word_tag_90, rare_90):
	#this function resets the list during the k fold cross validation
	word_occurences_90 = []	
	tag_occurences_90 = []
	word_tag_occurences_90 = []
	tag_next_tag_occurences_90 = []
	probability_tag_90 = []
	probability_word_tag_90 = []
	rare_90 = []


def kFoldCrossValidation(numberOfSentencesPerFold, dictionaries):

	from fold import Fold
	listOfFolds = {}

	#create 10 folds
	file_list = list(dictionaries.frequency_sentences.keys())

	filePointer = 0
	startLine = 1
	endLine = 0
	finishedLoop = False

	''''for i in range(0,10):
		sentenceCount = 0 
		fold = Fold(i)
		fold.startLine = startLine 
		while sentenceCount != numberOfSentencesPerFold :
			if sentenceCount + dictionaries.frequency_sentences[file_list[filePointer]] > numberOfSentencesPerFold:

				if file_list[filePointer] == "12/WSJ_1299":
					endLine = 0
				else:
					endLine = numberOfSentencesPerFold - sentenceCount
						
				fold.addFileName(file_list[filePointer])
				fold.endLine = endLine 
				startLine = endLine + 1
				endLine = 0
				finishedLoop = True
				break 
			else:

				if startLine != 0 and finishedLoop == True:
					sentenceCount = sentenceCount + (dictionaries.frequency_sentences[file_list[filePointer]] - (startLine - 1))
					finishedLoop = False
				else:
					sentenceCount = sentenceCount + dictionaries.frequency_sentences[file_list[filePointer]]
	
				fold.addFileName(file_list[filePointer])
				if file_list[filePointer] == "12/WSJ_1299":
					fold.endLine = 0
					break
				filePointer += 1 

		listOfFolds.append(fold)'''

	pointer = 0
	sentenceCount = 0	
	for i in range(0,10):
		fold = Fold(i)

		if i == 9:
			for j in range(pointer,len(dictionaries.sentences)):
				fold.sentences.append(dictionaries.sentences[pointer])
				pointer += 1
				sentenceCount += 1
		else:
			while sentenceCount <= numberOfSentencesPerFold:
				fold.sentences.append(dictionaries.sentences[pointer])
				pointer += 1
				sentenceCount += 1

		sentenceCount = 0	
		listOfFolds[i] = fold

	for i in range(0,10):
		print("Sentence count of fold " + `i`  + " = " + `len(listOfFolds[i].sentences)`)
		
	#start training and testing with these 10 folds 
	accuracy_90 = {}
	accuracy_100 = {}

	for i in range(0,10):
		fold_to_test = listOfFolds[i]

		for j in range(0,10):
			if i != j:
				#train the 90% corpus excluding the the fold at i
				print("Training ====>>>>>>>>")
				for k in range(0, len(listOfFolds[j].sentences)):
					countOccurences(listOfFolds[j].sentences[k], dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.trigram_occurences_90)				

		calculateProbabilities(dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.probability_tag_90, dictionaries.probability_word_tag_90)

		acc_90_list = []
		acc_100_list = []

		#Test using the fold i and store the accuracy in the dictionaries to be calculated at the last
		print("Testing ============>>>>>")
		for j in range(0, len(listOfFolds[i].sentences)):
			print("Running sentence : " + `j`)
			line = listOfFolds[i].sentences[j]			
			if line != "\n" and line != " " and line != "":
				predicted_tags_100 = viterbi(removeTags(line), dictionaries.word_occurences_100, dictionaries.tag_occurences_100, dictionaries.word_tag_occurences_100, dictionaries.tag_next_tag_occurences_100, dictionaries.probability_tag_100, dictionaries.probability_word_tag_100, dictionaries.rare_words_100, dictionaries.trigram_occurences_100)
				predicted_tags_90 = viterbi(removeTags(line), dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.probability_tag_90, dictionaries.probability_word_tag_90, dictionaries.rare_words_90, dictionaries.trigram_occurences_90)	
							
				acc_90 = calculateAccuracy(getTags(line),predicted_tags_90)
				acc_100 = calculateAccuracy(getTags(line),predicted_tags_100)

				acc_90_list.append(acc_90)
				acc_100_list.append(acc_100) ;	
		
		print("Accuracy for fold " + str(i) + " with 90 training is " + ` sum(acc_90_list) / float(len(acc_90_list))  ` + "%" + " and with 100 training is " + `sum(acc_100_list) / float(len(acc_100_list))`)

		accuracy_90[i] = acc_90_list
		accuracy_100[i] = acc_100_list				
		cleanList(dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.probability_tag_90, dictionaries.probability_word_tag_90,  dictionaries.rare_words_90)	
								
	#Loop through the number of folds and calculate the average accuracies for each fold for both 90/10 and 100/10 data								
	for i in range(0,10):
		print("Accuracy for fold " + str(i) + " with 90 training is " + ` sum(accuracy_90[i]) / float(len(accuracy_90[i]))  ` + "%" + " and with 100 training is " + `sum(accuracy_100[i]) / float(len(accuracy_100[i]))`)
	

def testOnNumberOfSentences(dictionaries):

	#THis function just test on x number of sentences from fold 0
	numberOfSentences = 2314

	acc_90_list = []
	acc_100_list = []

	for i in range(2315, len(dictionaries.sentences)):
		countOccurences(dictionaries.sentences[i], dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.trigram_occurences_90)
	
	findRareWords(dictionaries.word_tag_occurences_90, dictionaries.rare_words_90)  
	calculateProbabilities(dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.probability_tag_90, dictionaries.probability_word_tag_90)


	print("Testing ==========================>>>>>>>>>")

	for i in range(0,numberOfSentences):

		print("Count ===>>>  "  + `i`)
		if dictionaries.sentences[i] == "" or dictionaries.sentences[i] == " ":
			continue ;

		predicted_tags_100 = viterbi(removeTags(dictionaries.sentences[i]), dictionaries.word_occurences_100, dictionaries.tag_occurences_100,dictionaries.word_tag_occurences_100, dictionaries.tag_next_tag_occurences_100, dictionaries.probability_tag_100, dictionaries.probability_word_tag_100, dictionaries.rare_words_100, dictionaries.trigram_occurences_100)
		predicted_tags_90 = viterbi(removeTags(dictionaries.sentences[i]), dictionaries.word_occurences_90, dictionaries.tag_occurences_90, dictionaries.word_tag_occurences_90, dictionaries.tag_next_tag_occurences_90, dictionaries.probability_tag_90, dictionaries.probability_word_tag_90,dictionaries.rare_words_90, dictionaries.trigram_occurences_90)					
		acc_90 = calculateAccuracy(getTags(dictionaries.sentences[i]),predicted_tags_90)
		acc_100 = calculateAccuracy(getTags(dictionaries.sentences[i]),predicted_tags_100)
		acc_90_list.append(acc_90)
		acc_100_list.append(acc_100) ;	

	print("Average accuracy with corpus 90/10 : " + `sum(acc_90_list) / float(len(acc_90_list))` + "%")
	print("Average accuracy with copus 100/100 : " + `sum(acc_100_list) / float(len(acc_100_list))` + "%")


def main(full):

	from dictionaries import Dictionaries
	dictionaries = Dictionaries()

	totalSentences = cleanFile(dictionaries.word_occurences_100, dictionaries.tag_occurences_100, dictionaries.word_tag_occurences_100, dictionaries.tag_next_tag_occurences_100, dictionaries.trigram_occurences_100, dictionaries.frequency_sentences,dictionaries.sentences)
	numberOfSentencesPerFold = int(math.floor(totalSentences / 10))
	
	findRareWords(dictionaries.word_tag_occurences_100, dictionaries.rare_words_100)
	#training 100% data
	calculateProbabilities(dictionaries.word_occurences_100, dictionaries.tag_occurences_100, dictionaries.word_tag_occurences_100, dictionaries.tag_next_tag_occurences_100, dictionaries.probability_tag_100, dictionaries.probability_word_tag_100)
 

	if full == '0':
		testOnNumberOfSentences(dictionaries)
	elif full == '1':
		kFoldCrossValidation(numberOfSentencesPerFold,dictionaries)

def unitTesting():
	#testing methods getTags, calculateAccuracy, getLine
	line = "Mr./NNP Volk\/King/NNP 55/CD years/NNS old/JJ succeeds/VBZ Duncan/NNP Dwight/NNP who/WP retired/VBD in/IN September/NNP"
	print("Line : " + removeTags(line))
	print("Tags are "  )
	print(getTags(line))
	predicted_tags = ["NNP", "VP","CP" ,"NNS", "PP", "VBZ", "NP", "VP", "WP", "VBD", "IN", "NNP"]
	print("Predicted tags are ")
	print(predicted_tags)
	print("Accuracy is " + str(calculateAccuracy(getTags(line),predicted_tags)))
	print("List cleaned")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Please type python <filename> 1|0 where 1 = run full cross validation and 0 = run only on number of sentences")
		exit()
	main(sys.argv[1])