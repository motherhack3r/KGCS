from pathlib import Path

nodes_path = Path('tmp/combined-nodes.ttl')
rels_path = Path('tmp/combined-rels.ttl')


def scan_file_for_flags(path, max_lines=0):
    has_type = set()
    has_literal = set()
    sample_literals = {}  # subj -> list of (pred,obj)
    total = 0
    if not path.exists():
        print(f"Missing file: {path}")
        return has_type, has_literal, sample_literals
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('@') or line.startswith('#'):
                continue
            parts = line.split(' ', 2)
            if len(parts) < 3:
                continue
            subj, pred, obj = parts
            obj = obj.rstrip(' .')
            total += 1
            # detect rdf:type predicate
            if ('rdf-syntax-ns#type' in pred) or ('rdf:type' in pred) or pred == 'a':
                has_type.add(subj)
            # detect literal object
            if obj.startswith('"') or obj.startswith("'"):
                has_literal.add(subj)
                if subj not in sample_literals and len(sample_literals) < 2000:
                    sample_literals[subj] = [(pred, obj)]
                elif subj in sample_literals and len(sample_literals[subj]) < 5:
                    sample_literals[subj].append((pred, obj))
            if max_lines and total > max_lines:
                break
    return has_type, has_literal, sample_literals


def main():
    print('Scanning nodes file for rdf:type and literal occurrences (stream)...')
    ntypes, nlits, sample_literals_nodes = scan_file_for_flags(nodes_path)
    print(f'  nodes: rdf:type count={len(ntypes):,}, subjects with literals={len(nlits):,}')

    print('Scanning rels file for rdf:type (to detect misclassified type triples)...')
    rtypes, rlits, sample_literals_rels = scan_file_for_flags(rels_path)
    print(f'  rels: rdf:type count={len(rtypes):,}, subjects with literals={len(rlits):,}')

    # Find up to 10 subjects that have literals in nodes but no type in nodes
    candidates = [s for s in sorted(list(nlits)) if s not in ntypes]
    print(f'Found {len(candidates)} candidate subjects with literals but no rdf:type in nodes (showing up to 10)')
    limit = 10
    for subj in candidates[:limit]:
        print('\n---')
        print('Subject:', subj)
        print('Type in nodes?:', 'Yes' if subj in ntypes else 'No')
        print('Type in rels?:', 'Yes' if subj in rtypes else 'No')
        print('\nSample literal triples from nodes (predicate, object):')
        for p, o in sample_literals_nodes.get(subj, [])[:5]:
            print(' ', p, o)
        # show any rels triples referencing this subject (in rels file) - first 5
        count = 0
        print('\nMatching lines in rels file (first 5):')
        with open(rels_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                if subj in line and not line.strip().startswith('@'):
                    print(' ', line.strip())
                    count += 1
                    if count >= 5:
                        break

    # If no candidates, try reverse: subjects with rdf:type in rels but literals in nodes
    if not candidates:
        print('\nNo direct candidates found. Searching for subjects with rdf:type present only in rels (i.e., types misclassified)')
        suspects = [s for s in sorted(list(rtypes)) if s not in ntypes]
        print(f'  Found {len(suspects)} subjects with rdf:type in rels but not in nodes (showing up to 10)')
        for subj in suspects[:10]:
            print('\n---')
            print('Subject:', subj)
            # show sample nodes lines referencing subj
            print('Sample lines in nodes file (first 5):')
            cnt = 0
            with open(nodes_path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if subj in line and not line.strip().startswith('@'):
                        print(' ', line.strip())
                        cnt += 1
                        if cnt >= 5:
                            break
            print('Sample lines in rels file (first 5):')
            cnt = 0
            with open(rels_path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if subj in line and not line.strip().startswith('@'):
                        print(' ', line.strip())
                        cnt += 1
                        if cnt >= 5:
                            break

    print('\nScan complete.')

if __name__ == '__main__':
    main()
