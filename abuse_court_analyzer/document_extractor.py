"""
Document Text Extraction and Fact-Finding Module.

Extracts facts, names, dates, financial figures, legal references,
and patterns from court documents (local files or Google Drive).
"""

import re
import pandas as pd
from collections import Counter, defaultdict


class DocumentExtractor:
    """Extracts structured data and patterns from document text."""

    # Patterns for court document analysis
    PATTERNS = {
        "case_numbers": r'\b(?:\d{2,4}[-/][A-Z]{1,5}[-/]\d{3,8}|Case\s*(?:No\.?|#)\s*[\w-]+)\b',
        "dates": r'\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b',
        "money": r'\$[\d,]+(?:\.\d{2})?',
        "names_formal": r'\b(?:Hon(?:orable)?\.?\s+|Judge\s+|Attorney\s+|Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+|Dr\.?\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        "statutes": r'\b\d+\s+(?:U\.?S\.?C\.?|USC)\s*§?\s*\d+[a-z]?\b|\b§\s*\d+[-.\d]*\b',
        "court_orders": r'(?:IT IS (?:HEREBY )?ORDERED|ORDER(?:ED)?|DECREE[DS]?|JUDGMENT|RULING)',
        "legal_terms": r'\b(?:motion|petition|order|subpoena|affidavit|stipulation|'
                        r'contempt|custody|visitation|alimony|support|hearing|trial|'
                        r'appeal|discovery|deposition|mediation|arbitration|guardian\s*ad\s*litem)\b',
    }

    def __init__(self):
        self.extracted_data = []
        self.all_names = Counter()
        self.all_dates = []
        self.all_amounts = []
        self.document_index = []

    def extract_from_text(self, text, source_name="Unknown"):
        """
        Extract all structured data from a document's text.

        Returns dict with extracted entities and their contexts.
        """
        if not text or len(text.strip()) < 10:
            return {"source": source_name, "error": "No text content"}

        result = {
            "source": source_name,
            "text_length": len(text),
            "case_numbers": self._find_all(self.PATTERNS["case_numbers"], text),
            "dates": self._find_all(self.PATTERNS["dates"], text),
            "monetary_amounts": self._find_all(self.PATTERNS["money"], text),
            "named_individuals": self._extract_names(text),
            "statutes_cited": self._find_all(self.PATTERNS["statutes"], text),
            "court_orders": self._find_with_context(self.PATTERNS["court_orders"], text),
            "legal_terms_used": self._find_all(self.PATTERNS["legal_terms"], text, ignore_case=True),
            "key_facts": self._extract_key_facts(text),
            "allegations": self._extract_allegations(text),
            "rulings": self._extract_rulings(text),
        }

        # Accumulate for cross-document analysis
        self.extracted_data.append(result)
        self.all_names.update(result["named_individuals"])
        self.all_dates.extend(result["dates"])
        self.all_amounts.extend(result["monetary_amounts"])
        self.document_index.append({
            "source": source_name,
            "num_entities": sum(len(v) for v in result.values() if isinstance(v, list)),
            "text_length": len(text),
        })

        return result

    def extract_from_documents(self, documents):
        """
        Process multiple documents (list of dicts with 'name' and 'text').
        """
        results = []
        for doc in documents:
            name = doc.get("name", doc.get("title", "Unknown"))
            text = doc.get("text", "")
            results.append(self.extract_from_text(text, source_name=name))
        return results

    def get_cross_document_analysis(self):
        """Analyze patterns across all processed documents."""
        if not self.extracted_data:
            return {"error": "No documents processed"}

        # Most mentioned names
        top_names = self.all_names.most_common(30)

        # All unique case numbers
        all_case_nums = set()
        for d in self.extracted_data:
            all_case_nums.update(d.get("case_numbers", []))

        # Financial summary
        amounts = []
        for amt_str in self.all_amounts:
            try:
                val = float(amt_str.replace("$", "").replace(",", ""))
                amounts.append(val)
            except ValueError:
                pass

        # Legal terms frequency
        all_terms = Counter()
        for d in self.extracted_data:
            all_terms.update(t.lower() for t in d.get("legal_terms_used", []))

        # Statute frequency
        all_statutes = Counter()
        for d in self.extracted_data:
            all_statutes.update(d.get("statutes_cited", []))

        return {
            "total_documents": len(self.extracted_data),
            "most_mentioned_names": dict(top_names),
            "unique_case_numbers": list(all_case_nums),
            "financial_summary": {
                "total_amounts_found": len(amounts),
                "total_value": round(sum(amounts), 2) if amounts else 0,
                "min_amount": round(min(amounts), 2) if amounts else 0,
                "max_amount": round(max(amounts), 2) if amounts else 0,
                "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
            },
            "legal_terms_frequency": dict(all_terms.most_common(20)),
            "statutes_cited": dict(all_statutes.most_common(20)),
            "document_summary": self.document_index,
        }

    def build_person_registry(self):
        """Build a registry of all persons mentioned across documents."""
        registry = defaultdict(lambda: {
            "mentions": 0,
            "documents": set(),
            "contexts": [],
            "associated_roles": set(),
        })

        role_patterns = {
            "judge": r"(?:judge|hon(?:orable)?\.?)\s+",
            "attorney": r"(?:attorney|counsel|esq\.?)\s+",
            "guardian_ad_litem": r"(?:guardian\s+ad\s+litem|GAL)\s+",
            "petitioner": r"(?:petitioner|plaintiff)\s+",
            "respondent": r"(?:respondent|defendant)\s+",
        }

        for doc_data in self.extracted_data:
            source = doc_data["source"]
            text = ""
            # Get original text from context
            for name in doc_data.get("named_individuals", []):
                registry[name]["mentions"] += 1
                registry[name]["documents"].add(source)

        # Convert sets to lists for serialization
        result = {}
        for name, info in registry.items():
            result[name] = {
                "mentions": info["mentions"],
                "documents": list(info["documents"]),
                "num_documents": len(info["documents"]),
                "associated_roles": list(info["associated_roles"]),
            }

        return dict(sorted(result.items(), key=lambda x: x[1]["mentions"], reverse=True))

    # ------------------------------------------------------------------
    # Internal extraction methods
    # ------------------------------------------------------------------

    def _find_all(self, pattern, text, ignore_case=False):
        """Find all matches for a regex pattern."""
        flags = re.IGNORECASE if ignore_case else 0
        matches = re.findall(pattern, text, flags)
        return list(set(matches))

    def _find_with_context(self, pattern, text, context_chars=150):
        """Find matches with surrounding context."""
        results = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - context_chars)
            end = min(len(text), match.end() + context_chars)
            results.append({
                "match": match.group(),
                "context": text[start:end].strip(),
            })
        return results[:20]

    def _extract_names(self, text):
        """Extract person names from text."""
        # Formal titles
        formal = re.findall(self.PATTERNS["names_formal"], text)

        # Capitalized name pairs (first last)
        caps = re.findall(r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\b', text)

        # Filter out common false positives
        stop_names = {
            "united states", "supreme court", "district court", "family court",
            "superior court", "circuit court", "the court", "state of",
            "county of", "in the", "motion to", "order of", "guardian ad",
        }

        all_names = set(formal) | set(caps)
        filtered = [n for n in all_names if n.lower() not in stop_names and len(n) > 4]
        return filtered

    def _extract_key_facts(self, text):
        """Extract key factual statements."""
        facts = []
        fact_indicators = [
            r'(?:the\s+(?:court\s+)?finds?\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:it\s+is\s+(?:un)?disputed\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:the\s+evidence\s+(?:shows?|demonstrates?|establishes?)\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:(?:petitioner|respondent|plaintiff|defendant)\s+(?:alleges?|states?|testif(?:ied|ies))\s+(?:that\s+)?)(.*?)(?:\.|$)',
        ]

        for pattern in fact_indicators:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                fact = match.group(1).strip()
                if len(fact) > 20:
                    facts.append(fact[:300])

        return facts[:30]

    def _extract_allegations(self, text):
        """Extract allegations from text."""
        allegation_patterns = [
            r'(?:alleg(?:es?|ation|ed|ing)\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:claim(?:s|ed|ing)?\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:accus(?:es?|ed|ing)\s+(?:of\s+)?)(.*?)(?:\.|$)',
        ]

        allegations = []
        for pattern in allegation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                allegation = match.group(1).strip()
                if len(allegation) > 15:
                    allegations.append(allegation[:300])

        return allegations[:20]

    def _extract_rulings(self, text):
        """Extract court rulings and orders."""
        ruling_patterns = [
            r'(?:(?:IT IS )?(?:HEREBY )?ORDERED\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:the\s+court\s+(?:hereby\s+)?(?:orders?|rules?|decrees?|grants?|denies?)\s+(?:that\s+)?)(.*?)(?:\.|$)',
            r'(?:(?:GRANTED|DENIED|SUSTAINED|OVERRULED)[.:]?\s*)(.*?)(?:\.|$)',
        ]

        rulings = []
        for pattern in ruling_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ruling = match.group(1).strip()
                if len(ruling) > 10:
                    rulings.append(ruling[:300])

        return rulings[:20]
