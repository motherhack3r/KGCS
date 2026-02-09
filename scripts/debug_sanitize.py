from pathlib import Path
from scripts.combine_ttl_pipeline import combine_ttl_files
import tempfile
p=Path(tempfile.mkdtemp())
inp=p/'inp'; inp.mkdir()
f=inp/'pipeline-stage-byte.ttl'
f.write_text('@prefix ex: <https://example.org/> .\n<https://example.org/s3> a <https://example.org/Type> .\n<https://example.org/s3> <https://example.org/prop> "This has a byte repr b\\'\\x00\\x01\\x02\\' inside" .\n',encoding='utf-8')
nodes_out=p/'nodes_out2.ttl'
rels_out=p/'rels_out2.ttl'
full_out=p/'full_out2.ttl'
combine_ttl_files(nodes_out=str(nodes_out), rels_out=str(rels_out), heuristic_threshold=1, inputs=[str(inp)], full_out=str(full_out))
print('--- nodes_out ---')
print(nodes_out.read_text())
print('--- full_out ---')
print(full_out.read_text())
