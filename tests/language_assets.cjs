// Public data/assets only; no site or credential reads.
const fs=require('fs'),assert=require('assert/strict'),path=require('path'),{getCountries}=require('../frontend/node_modules/libphonenumber-js');
const root=path.resolve(__dirname,'..'),flags=root+'/frontend/public/flags/',display=JSON.parse(fs.readFileSync(root+'/frontend/src/reference-data/care-language-display.json'));
for(const country of getCountries())assert(fs.existsSync(flags+country.toLowerCase()+'.svg'),'Missing phone-country flag: '+country);
for(const[code,language]of Object.entries(display)){assert(language.english&&language.english!==code,'Missing full catalog name');if(language.region)assert(fs.existsSync(flags+language.region.toLowerCase()+'.svg'),'Missing language-region flag');}
assert.equal(Object.keys(display).length,630);assert(fs.existsSync(flags+'LICENSE.txt'));console.log('PASS full names for630 languages and local flag coverage for all '+getCountries().length+' supported phone countries, including AC/TA.');
