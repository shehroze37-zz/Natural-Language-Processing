import collections

class Dictionaries:
	word_occurences_90 = {}
	word_occurences_100 = {}
	tag_occurences_90 = {}
	tag_occurences_100 = {}
	word_tag_occurences_90 = {}
	word_tag_occurences_100 = {}
	tag_next_tag_occurences_90 = {}
	tag_next_tag_occurences_100 = {}
	frequency_sentences = collections.OrderedDict()
	probability_tag_90 = {}
	probability_tag_100 = {}
	probability_word_tag_90 = {}
	probability_word_tag_100 = {}
	trigram_occurences_100 = {}
	trigram_occurences_90 = {}
	sentences = []
	rare_words_100 = {}
	rare_words_90 = {}

	def __init__(self):
		self.sentences = []          