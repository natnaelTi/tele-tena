"""Prove translated-throw plumbing did not change other authorization/business ASTs."""
import ast,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='1dca1ff03e3c344d1a14a5026d4372ef318ef5b8'
class Rewrite(ast.NodeTransformer):
 def visit_Call(self,node):
  self.generic_visit(node)
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='frappe' and node.func.attr=='throw':node.func=ast.Name(id='localized_throw',ctx=ast.Load())
  return node
class Equivalence(unittest.TestCase):
 def test_permission_and_business_trees_only_replace_throw_target(self):
  files=subprocess.check_output(['git','diff','--name-only',BASE,'--','tele_tena'],cwd=ROOT,text=True).splitlines();count=0
  skip={'tele_tena/localization/__init__.py','tele_tena/api/journey.py','tele_tena/api/extensions.py','tele_tena/api/service_catalog.py'}
  for name in files:
   if name in skip or not name.endswith('.py'):continue
   original=ast.parse(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT,text=True));current=ast.parse((ROOT/name).read_text());original=Rewrite().visit(original)
   current.body=[n for n in current.body if not(isinstance(n,ast.ImportFrom) and n.module=='tele_tena.localization' and [a.name for a in n.names]==['localized_throw'])]
   self.assertEqual(ast.dump(original),ast.dump(current),name);count+=1
  self.assertGreaterEqual(count,40)
if __name__=='__main__':unittest.main()
