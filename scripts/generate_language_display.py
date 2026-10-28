"""Regenerate public language display metadata from shipped CLDR names and Babel2.16.
No site/credential reads. Language-region hints are illustrative, never nationality.
"""
import json
from pathlib import Path
import babel
from babel.core import get_global
assert babel.__version__=='2.16.0','Use the recorded Babel2.16 source version'
ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'tele_tena/reference_data/care-languages-v1.json').read_text())
local=set(get_global('territory_languages')['ET'])
records={}
for row in source['records']:
 code=row['code'];likely=get_global('likely_subtags').get(code,'').split('_');region=likely[-1] if likely else ''
 if code in local and code!='en':region='ET'
 if len(region)!=2 or not region.isalpha():region=None
 records[code]={'english':row['english'],'region':region,'priority':code in local}
result={'source':'Unicode CLDR names, likely subtags and Ethiopia territory-language data via Babel2.16.0','source_url':'https://cldr.unicode.org/','license_url':'https://www.unicode.org/license.txt','note':'Regions are visual associations, not exclusive language countries or authorization. English and existing Ethiopia territory languages are grouped first; not an exhaustive Ethiopian language inventory.','records':records}
(ROOT/'tele_tena/reference_data/care-language-display-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
# Small public label/region map makes names independent of the browser CLDR version.
target=ROOT/'frontend/src/reference-data/care-language-display.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(records,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
print('Named languages:',len(records),'Priority languages:',sum(r['priority'] for r in records.values()))
