// Parse source only; never evaluate app modules or read sites/private records.
const fs=require('fs'),path=require('path'),ts=require('../../frontend/node_modules/typescript'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),entries=[],translations={},excluded=[];
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?walk(path.join(dir,x.name)):[path.join(dir,x.name)]);}
function add(english,file,node,context){if(!english?.trim())return;entries.push({english,source_location:path.relative(root,file)+':'+node.getSourceFile().getLineAndCharacterOfPosition(node.getStart()).line,context});}
function human(s){return /[A-Za-z]/.test(s)&&s.length>1&&s.length<10000&&!/^(?:https?:|[./#]|\w+@|--|SELECT |INSERT |UPDATE |DELETE |CREATE |ALTER )/i.test(s)&&!/[{}<>][^ ]*[{}<>]/.test(s)&&(/\s/.test(s)||/^[A-Z][a-z]+(?:[A-Z][a-z]+)*[.!?…]?$/.test(s));}
function technical(node){
 for(let n=node;n;n=n.parent){
  if(ts.isLiteralTypeNode(n))return 'Type-only identifier; not rendered copy';
  if(ts.isJsxAttribute(n)&&(['className','id','role','type','name','value','htmlFor','aria-controls','aria-labelledby','aria-describedby','autoComplete','inputMode','pattern','d','viewBox'].includes(n.name.getText())||n.name.getText().startsWith('data-')))return 'Technical JSX attribute '+n.name.getText();
  if(ts.isJsxElement(n)||ts.isSourceFile(n))break;
 }
 if(ts.isBinaryExpression(node.parent)){const other=node.parent.left===node?node.parent.right:node.parent.left;if(/\.(key|code)$/.test(other.getText()))return 'Keyboard or machine-code comparison';}
 return null;
}
for(const file of walk(root+'/frontend/src').filter(f=>/\.(tsx?|json)$/.test(f)&&!f.includes('/localization/'))){if(file.endsWith('.json'))continue;const source=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,file.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS);
 function visit(n){if(ts.isVariableDeclaration(n)&&['am','om'].includes(n.name.getText(source))&&file.endsWith('/i18n.ts'))return;if(ts.isPropertyAssignment(n)&&['am','om'].includes(n.name.getText(source).replace(/["']/g,''))&&ts.isObjectLiteralExpression(n.initializer))return;if(/translations|useLocale/.test(file)&&ts.isPropertyAssignment(n)&&ts.isArrayLiteralExpression(n.initializer)&&n.initializer.elements.length===2&&n.initializer.elements.every(ts.isStringLiteralLike)){const english=ts.isStringLiteralLike(n.name)?n.name.text:n.name.getText(source);translations[english]=n.initializer.elements.map(x=>x.text);add(english,file,n,'Shared UI Copy');return;}
 if(ts.isStringLiteralLike(n)){const explicit=ts.isCallExpression(n.parent)&&n.parent.arguments[0]===n&&['w','text','fail'].includes(n.parent.expression.getText(source));if(explicit||human(n.text)){const reason=explicit?null:technical(n);if(reason)excluded.push({english:n.text,source_location:path.relative(root,file)+':'+n.getSourceFile().getLineAndCharacterOfPosition(n.getStart()).line,reason});else add(n.text,file,n,path.basename(file).replace(/\..*/,''));}}
 if(ts.isJsxText(n)&&n.text.trim())add(n.text.replace(/\s+/g,' ').trim(),file,n,path.basename(file).replace(/\..*/,''));
 if(ts.isTemplateExpression(n)&&human(n.head.text)){let message=n.head.text;for(const x of n.templateSpans)message+='{'+x.expression.getText(source)+'}'+x.literal.text;add(message,file,n,path.basename(file).replace(/\..*/,''));}
 ts.forEachChild(n,visit);}visit(source);
 if(file.endsWith('/i18n.ts')){const tables={};for(const statement of source.statements)if(ts.isVariableStatement(statement))for(const d of statement.declarationList.declarations){const name=d.name.getText(source);if(['en','am','om'].includes(name)&&d.initializer&&ts.isObjectLiteralExpression(d.initializer)){tables[name]={};for(const p of d.initializer.properties)if(ts.isPropertyAssignment(p)&&ts.isStringLiteralLike(p.initializer))tables[name][p.name.getText(source).replace(/[\"']/g,'')]=p.initializer.text;}}for(const [key,english]of Object.entries(tables.en||{}))translations[english]=[tables.am?.[key]||'',tables.om?.[key]||''];}
}
process.stdout.write(JSON.stringify({entries,translations,excluded}));
