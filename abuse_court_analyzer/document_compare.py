"""
Document Comparison and Side-by-Side Analysis Module.

Compares two court documents to find similarities, differences,
contradictions, and patterns across case records.
"""

import re
from difflib import SequenceMatcher, unified_diff
from collections import Counter


class DocumentComparer:
    """Compare two documents side by side with forensic analysis."""

    def __init__(self):
        self.comparisons = []

    def compare(self, doc_a, doc_b, label_a="Document A", label_b="Document B"):
        """
        Full comparison of two documents.

        Args:
            doc_a: dict with 'title' and 'text' keys (or plain string)
            doc_b: dict with 'title' and 'text' keys (or plain string)
            label_a: Label for first document
            label_b: Label for second document

        Returns:
            dict with comparison results
        """
        text_a = doc_a["text"] if isinstance(doc_a, dict) else str(doc_a)
        text_b = doc_b["text"] if isinstance(doc_b, dict) else str(doc_b)
        title_a = doc_a.get("title", label_a) if isinstance(doc_a, dict) else label_a
        title_b = doc_b.get("title", label_b) if isinstance(doc_b, dict) else label_b

        result = {
            "document_a": title_a,
            "document_b": title_b,
            "similarity_score": self._similarity_score(text_a, text_b),
            "text_diff": self._generate_diff(text_a, text_b, title_a, title_b),
            "shared_entities": self._find_shared_entities(text_a, text_b),
            "contradictions": self._find_contradictions(text_a, text_b),
            "unique_to_a": self._find_unique_claims(text_a, text_b),
            "unique_to_b": self._find_unique_claims(text_b, text_a),
            "date_comparison": self._compare_dates(text_a, text_b),
            "monetary_comparison": self._compare_amounts(text_a, text_b),
            "side_by_side": self._build_side_by_side(text_a, text_b, title_a, title_b),
        }

        self.comparisons.append(result)
        return result

    def _similarity_score(self, text_a, text_b):
        """Calculate overall similarity between two texts."""
        # Use sentence-level comparison for more meaningful score
        sents_a = self._split_sentences(text_a)
        sents_b = self._split_sentences(text_b)

        if not sents_a or not sents_b:
            return 0.0

        # Find best match for each sentence in A against B
        match_scores = []
        for sa in sents_a:
            best = max(SequenceMatcher(None, sa.lower(), sb.lower()).ratio()
                       for sb in sents_b)
            match_scores.append(best)

        return round(sum(match_scores) / len(match_scores), 4)

    def _generate_diff(self, text_a, text_b, title_a, title_b):
        """Generate a unified diff between two documents."""
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)

        diff = list(unified_diff(
            lines_a, lines_b,
            fromfile=title_a, tofile=title_b,
            lineterm=""
        ))
        return "\n".join(diff[:500])  # Cap at 500 lines

    def _find_shared_entities(self, text_a, text_b):
        """Find names, dates, and amounts that appear in both documents."""
        entities_a = self._extract_entities(text_a)
        entities_b = self._extract_entities(text_b)

        shared = {}
        for entity_type in entities_a:
            set_a = set(entities_a[entity_type])
            set_b = set(entities_b.get(entity_type, []))
            common = set_a & set_b
            if common:
                shared[entity_type] = list(common)

        return shared

    def _find_contradictions(self, text_a, text_b):
        """Detect potential contradictions between documents."""
        contradictions = []

        # Date contradictions: same event, different dates
        dates_a = self._extract_dates(text_a)
        dates_b = self._extract_dates(text_b)

        # Amount contradictions
        amounts_a = self._extract_amounts(text_a)
        amounts_b = self._extract_amounts(text_b)
        if amounts_a and amounts_b:
            for amt_a in amounts_a:
                for amt_b in amounts_b:
                    if amt_a != amt_b:
                        # Check if surrounding context is similar
                        contradictions.append({
                            "type": "AMOUNT_DISCREPANCY",
                            "doc_a_value": amt_a,
                            "doc_b_value": amt_b,
                        })

        # Negation contradictions
        sents_a = self._split_sentences(text_a)
        sents_b = self._split_sentences(text_b)
        negation_words = {"not", "never", "no", "didn't", "wasn't", "isn't",
                          "denied", "denies", "false", "untrue"}

        for sa in sents_a:
            for sb in sents_b:
                sim = SequenceMatcher(None, sa.lower(), sb.lower()).ratio()
                if 0.4 < sim < 0.85:
                    words_a = set(sa.lower().split())
                    words_b = set(sb.lower().split())
                    neg_a = words_a & negation_words
                    neg_b = words_b & negation_words
                    if neg_a != neg_b:
                        contradictions.append({
                            "type": "POTENTIAL_CONTRADICTION",
                            "doc_a_statement": sa.strip()[:200],
                            "doc_b_statement": sb.strip()[:200],
                            "similarity": round(sim, 3),
                        })

        return contradictions[:20]  # Top 20

    def _find_unique_claims(self, text_primary, text_other):
        """Find statements in primary that have no close match in other."""
        sents_primary = self._split_sentences(text_primary)
        sents_other = self._split_sentences(text_other)

        if not sents_primary or not sents_other:
            return []

        unique = []
        for sp in sents_primary:
            if len(sp.strip()) < 20:
                continue
            best_match = max(
                SequenceMatcher(None, sp.lower(), so.lower()).ratio()
                for so in sents_other
            )
            if best_match < 0.3:
                unique.append(sp.strip()[:300])

        return unique[:30]

    def _compare_dates(self, text_a, text_b):
        """Compare dates mentioned in both documents."""
        dates_a = self._extract_dates(text_a)
        dates_b = self._extract_dates(text_b)
        return {
            "dates_in_a": dates_a[:20],
            "dates_in_b": dates_b[:20],
            "shared_dates": list(set(dates_a) & set(dates_b)),
            "only_in_a": list(set(dates_a) - set(dates_b))[:10],
            "only_in_b": list(set(dates_b) - set(dates_a))[:10],
        }

    def _compare_amounts(self, text_a, text_b):
        """Compare monetary amounts mentioned in both documents."""
        amounts_a = self._extract_amounts(text_a)
        amounts_b = self._extract_amounts(text_b)
        return {
            "amounts_in_a": amounts_a,
            "amounts_in_b": amounts_b,
            "shared_amounts": list(set(amounts_a) & set(amounts_b)),
            "discrepancies": list(set(amounts_a).symmetric_difference(set(amounts_b))),
        }

    def _build_side_by_side(self, text_a, text_b, title_a, title_b, max_lines=200):
        """
        Build a side-by-side text representation.
        Returns list of dicts with 'line_a' and 'line_b' keys for Excel output.
        """
        lines_a = text_a.splitlines()[:max_lines]
        lines_b = text_b.splitlines()[:max_lines]

        max_len = max(len(lines_a), len(lines_b))
        rows = []
        for i in range(max_len):
            row = {
                "line_num": i + 1,
                title_a: lines_a[i] if i < len(lines_a) else "",
                title_b: lines_b[i] if i < len(lines_b) else "",
            }
            # Flag differences
            if i < len(lines_a) and i < len(lines_b):
                sim = SequenceMatcher(None, lines_a[i], lines_b[i]).ratio()
                row["match_score"] = round(sim, 2)
                row["flag"] = "MATCH" if sim > 0.8 else ("SIMILAR" if sim > 0.4 else "DIFFERENT")
            else:
                row["match_score"] = 0
                row["flag"] = "MISSING"
            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Entity extraction helpers
    # ------------------------------------------------------------------

    def _extract_entities(self, text):
        """Extract named entities from text using patterns."""
        return {
            "dates": self._extract_dates(text),
            "amounts": self._extract_amounts(text),
            "names": self._extract_names(text),
            "case_numbers": self._extract_case_numbers(text),
        }

    def _extract_dates(self, text):
        patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        ]
        dates = []
        for p in patterns:
            dates.extend(re.findall(p, text, re.IGNORECASE))
        return list(set(dates))

    def _extract_amounts(self, text):
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b',
        ]
        amounts = []
        for p in patterns:
            amounts.extend(re.findall(p, text))
        return list(set(amounts))

    def _extract_names(self, text):
        """Extract potential person names (capitalized word pairs)."""
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        names = re.findall(pattern, text)
        # Filter common non-name phrases
        stop_phrases = {"the court", "united states", "state of", "county of",
                        "superior court", "district court", "family court"}
        return [n for n in set(names) if n.lower() not in stop_phrases][:30]

    def _extract_case_numbers(self, text):
        patterns = [
            r'\b\d{2,4}-[A-Z]{1,3}-\d{3,8}\b',
            r'\bCase\s*(?:No\.?|#)\s*[\w-]+\b',
        ]
        case_nums = []
        for p in patterns:
            case_nums.extend(re.findall(p, text, re.IGNORECASE))
        return list(set(case_nums))

    def _split_sentences(self, text):
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
