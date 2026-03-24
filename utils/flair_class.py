from flair.data import Sentence
from flair.models import SequenceTagger
import sys
import io

class Flair_tools() :
    def __init__(
            self,
            text,
            tagger = SequenceTagger.load("flair/ner-english-large")
    
    ):
        self.text = text
        self.tagger = tagger
    
    def flair_redactor(self):

        entity_map ={}
        counter = {}

        sentence = Sentence(self.text)
        self.tagger.predict(sentence)

        # --- Redaction ---
        entity_map = {}  # label -> original text
        counters = {}    # track multiple entities of same type e.g. PER_1, PER_2
        spans = sorted(sentence.get_spans('ner'), key=lambda s: s.start_position, reverse=True)

        redacted_text = self.text
        for span in spans:
            tag = span.get_label('ner').value       # e.g. "PER", "LOC"
            counters[tag] = counters.get(tag, 0) + 1
            placeholder = f"[{tag}_{counters[tag]}]"
            entity_map[placeholder] = span.text
            redacted_text = redacted_text[:span.start_position] + placeholder + redacted_text[span.end_position:]

        return redacted_text, entity_map
    
    def flair_restorer(self, redacted_text, entity_map):
        restored_text = redacted_text
        for placeholder, original in entity_map.items():
            restored_text = restored_text.replace(placeholder, original)

        return restored_text
"""
if __name__ == "__main__":
    text = "Name: S. Bala Bala Sundren \nAccount: 001801030142\nBank: ICICI BANK\nType: Savings\nBranch: Trichy Road main, Coimbatore \nIFSC Code: ICIC0000016"
    flair = Flair_tools(text)
    redacted_text, entity_map = flair.flair_redactor()
    restored_text = flair.flair_restorer(redacted_text, entity_map)
    print(restored_text)
"""