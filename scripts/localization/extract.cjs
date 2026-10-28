// Parse source only; never evaluate app modules or read sites/private records.
const fs=require('fs'),path=require('path'),ts=require('../../frontend/node_modules/typescript'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),entries=[],translations={},excluded=[];
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?walk(path.join(dir,x.name)):[path.join(dir,x.name)]);}
function add(english,file,node,context){if(!english?.trim())return;entries.push({english,source_location:path.relative(root,file)+':'+node.getSourceFile().getLineAndCharacterOfPosition(node.getStart()).line,context});}
function human(s){return /[A-Za-z]/.test(s)&&s.length>1&&s.length<10000&&!/^(?:https?:|[./#]|\w+@|--|SELECT |INSERT |UPDATE |DELETE |CREATE |ALTER )/i.test(s)&&!/[{}<>][^ ]*[{}<>]/.test(s)&&(/\s/.test(s)||/^[A-Z][a-z]+(?:[A-Z][a-z]+)*[.!?…]?$/.test(s));}
function machineSelector(n){
 if(ts.isParenthesizedExpression(n)||ts.isAsExpression(n)||ts.isNonNullExpression(n))return machineSelector(n.expression);
 if(ts.isCallExpression(n)&&n.expression.getText()==='String'&&n.arguments.length===1)return machineSelector(n.arguments[0]);
 if(ts.isBinaryExpression(n)&&n.operatorToken.kind===ts.SyntaxKind.BarBarToken)return machineSelector(n.left);
 return /(?:^|\.)(?:\w+_)?(key|code|state|status|kind|phase|event|channel|decision|mode)$/.test(n.getText());
}
function technical(node){
 for(let n=node;n;n=n.parent){
  if(ts.isLiteralTypeNode(n))return 'Type-only identifier; not rendered copy';
  if(ts.isJsxAttribute(n)&&(['className','id','role','type','name','value','htmlFor','aria-controls','aria-labelledby','aria-describedby','autoComplete','inputMode','pattern','d','viewBox','style','transform','transformOrigin'].includes(n.name.getText())||n.name.getText().startsWith('data-')))return 'Technical JSX attribute '+n.name.getText();
  if(ts.isJsxElement(n)||ts.isSourceFile(n))break;
 }
 if(ts.isBinaryExpression(node.parent)){const other=node.parent.left===node?node.parent.right:node.parent.left;if(machineSelector(other))return 'Keyboard or machine-code comparison';}
 if(ts.isBinaryExpression(node.parent)&&node.parent.operatorToken.kind===ts.SyntaxKind.InKeyword)return 'Property-presence identifier';
 if(ts.isCallExpression(node.parent)&&/(?:^|\.)(querySelector|querySelectorAll|closest|getElementById|matchMedia)$/.test(node.parent.expression.getText()))return 'DOM selector or media query';
 let parent=node.parent;
 if(ts.isArrayLiteralExpression(parent)&&ts.isPropertyAccessExpression(parent.parent)&&ts.isCallExpression(parent.parent.parent)){
  const call=parent.parent.parent;if(parent.parent.name.text==='includes'&&call.arguments.some(machineSelector))return 'Keyboard or state matching set';
 }
 if(ts.isPropertyAssignment(node.parent)&&node.parent.initializer===node){
  const field=node.parent.name.getText().replace(/["']/g,'');
  if(['transform','transformOrigin'].includes(field)||node.getSourceFile().fileName.endsWith('/ClinicianHeroScene.tsx')&&['origin','wave'].includes(field))return 'SVG/CSS geometry value';
  if(['kind','source','event','state','status','channel'].includes(field)&&/[a-z][A-Z]/.test(node.text||''))return 'Machine event/state identifier; display title is separate';
 }
 if(node.getSourceFile().fileName.endsWith('/pages/Clinician.tsx')&&['PendingConfirmation','NoShow'].includes(node.text||'')&&ts.isArrayLiteralExpression(node.parent))return 'Appointment filter wire state; explicit display labels are separate';
 if(node.getSourceFile().fileName.endsWith('/PaymentActivityAlerts.tsx')){for(let n=node;n;n=n.parent){if(ts.isVariableDeclaration(n)&&n.name.getText()==='kinds')return 'Payment-event matching set';}}
 if(/\/hooks\/use(?:Locale|Session|Notifications)\.tsx$/.test(node.getSourceFile().fileName)&&['Missing locale provider','Missing session provider','Notification provider unavailable','Session unavailable'].includes(node.text||''))return 'Internal provider diagnostic; user-facing recovery copy is separate';
 if(node.getSourceFile().fileName.endsWith('/care-search.ts')&&node.text.startsWith('i me my am im have been'))return 'Legacy lexical stop-word data; not visible copy';
 if(node.getSourceFile().fileName.endsWith('/Admin.tsx')&&['audio\nvideo','direct-booking\nscheduled'].includes(node.text))return 'Controlled schema-key example; must retain wire values';
 return null;
}
for(const file of walk(root+'/frontend/src').filter(f=>/\.(tsx?|json)$/.test(f)&&!f.includes('/localization/'))){if(file.endsWith('.json'))continue;const source=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,file.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS);
 function visit(n){if(ts.isVariableDeclaration(n)&&['am','om'].includes(n.name.getText(source))&&file.endsWith('/i18n.ts'))return;if(ts.isPropertyAssignment(n)&&['am','om'].includes(n.name.getText(source).replace(/["']/g,''))&&ts.isObjectLiteralExpression(n.initializer))return;if(/translations|useLocale/.test(file)&&ts.isPropertyAssignment(n)&&ts.isArrayLiteralExpression(n.initializer)&&n.initializer.elements.length===2&&n.initializer.elements.every(ts.isStringLiteralLike)){const english=ts.isStringLiteralLike(n.name)?n.name.text:n.name.getText(source);translations[english]=n.initializer.elements.map(x=>x.text);add(english,file,n,'Shared UI Copy');return;}
 if(ts.isStringLiteralLike(n)){const explicit=ts.isCallExpression(n.parent)&&n.parent.arguments[0]===n&&['w','text','fail'].includes(n.parent.expression.getText(source));if(explicit||human(n.text)){const reason=explicit?null:technical(n);if(reason)excluded.push({english:n.text,source_location:path.relative(root,file)+':'+n.getSourceFile().getLineAndCharacterOfPosition(n.getStart()).line,reason});else add(n.text,file,n,path.basename(file).replace(/\..*/,''));}}
 if(ts.isJsxText(n)&&n.text.trim())add(n.text.replace(/\s+/g,' ').trim(),file,n,path.basename(file).replace(/\..*/,''));
 if(ts.isTemplateExpression(n)&&human(n.head.text)){let message=n.head.text;for(const x of n.templateSpans)message+='{'+x.expression.getText(source)+'}'+x.literal.text;const reason=technical(n);if(reason)excluded.push({english:message,source_location:path.relative(root,file)+':'+n.getSourceFile().getLineAndCharacterOfPosition(n.getStart()).line,reason});else add(message,file,n,path.basename(file).replace(/\..*/,''));}
 ts.forEachChild(n,visit);}visit(source);
 if(file.endsWith('/i18n.ts')){const tables={};for(const statement of source.statements)if(ts.isVariableStatement(statement))for(const d of statement.declarationList.declarations){const name=d.name.getText(source);if(['en','am','om'].includes(name)&&d.initializer&&ts.isObjectLiteralExpression(d.initializer)){tables[name]={};for(const p of d.initializer.properties)if(ts.isPropertyAssignment(p)&&ts.isStringLiteralLike(p.initializer))tables[name][p.name.getText(source).replace(/[\"']/g,'')]=p.initializer.text;}}for(const [key,english]of Object.entries(tables.en||{}))translations[english]=[tables.am?.[key]||'',tables.om?.[key]||''];}
}
process.stdout.write(JSON.stringify({entries,translations,excluded}));
