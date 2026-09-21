def detect_relationships(tables):
    rels = []
    names = list(tables)
    for i, left in enumerate(names):
        for right in names[i+1:]:
            common = set(map(str, tables[left].columns)) & set(map(str, tables[right].columns))
            for col in sorted(common):
                a, b = tables[left][col], tables[right][col]
                nonnull_a, nonnull_b = a.dropna(), b.dropna()
                if len(nonnull_a) == 0 or len(nonnull_b) == 0:
                    continue
                overlap = len(set(nonnull_a.astype(str).head(5000)) & set(nonnull_b.astype(str).head(5000)))
                denom = max(1, min(nonnull_a.nunique(), nonnull_b.nunique(), 5000))
                score = overlap / denom
                if score >= 0.25:
                    rels.append({"left": left, "right": right, "column": col, "confidence": "high" if score >= .7 else "medium", "score": score})
    return rels
