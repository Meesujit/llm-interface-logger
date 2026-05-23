from typing import Optional
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None

REDACT_ENTITIES = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "PERSON", "LOCATION"]
REPLACEMENT_MAP = {"EMAIL_ADDRESS": "<EMAIL>", "PHONE_NUMBER": "<PHONE>", "CREDIT_CARD": "<CREDIT_CARD>", "US_SSN": "<SSN>", "PERSON": "<PERSON>", "LOCATION": "<LOCATION>"}

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        nlp_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}
        _analyzer = AnalyzerEngine(nlp_engine=NlpEngineProvider(nlp_configuration=nlp_config).create_engine())
    return _analyzer

def _get_anonymizer():
    global _anonymizer
    if _anonymizer is None: _anonymizer = AnonymizerEngine()
    return _anonymizer

class PIIRedactor:
    def redact(self, text: str) -> str:
        if not text: return text
        try:
            analyzer = _get_analyzer()
            anonymizer = _get_anonymizer()
            results = analyzer.analyze(text=text, entities=REDACT_ENTITIES, language="en")
            if not results: return text
            operators = {e: {"type": "replace", "new_value": REPLACEMENT_MAP.get(e, f"<{e}>")} for e in REDACT_ENTITIES}
            return anonymizer.anonymize(text=text, analyzer_results=results, operators=operators).text
        except Exception:
            return text
