"""Read TJS literal tables as data, without evaluating game code."""
import re, ast
TOKEN=re.compile(r'\s+|//[^\n]*|/\*[\s\S]*?\*/|\(const\)|%\[|=>|[\[\],:;]|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|-?(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?)|[\w.]+')
def loads(text):
 tokens=[m.group() for m in TOKEN.finditer(text) if not (m.group().isspace() or m.group().startswith(('//','/*')) or m.group()=='(const)')];i=0
 def value():
  nonlocal i
  t=tokens[i];i+=1
  if t in ('%[','['):
   obj={} if t=='%[' else []
   while tokens[i]!=']':
    v=value()
    if isinstance(obj,dict):
     assert tokens[i] in ('=>',':');i+=1;obj[str(v)]=value()
    else:obj.append(v)
    if tokens[i]==',':i+=1
   i+=1;return obj
  if t.startswith(('"',"'")):return ast.literal_eval(t)
  if t in ('true','false'):return t=='true'
  if t in ('void','null'):return None
  try:return float(t) if '.' in t else int(t,0) if t.startswith('0x') else int(t)
  except ValueError:return t
 return value()
