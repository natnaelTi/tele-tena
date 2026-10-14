import assert from 'node:assert/strict';
import { careSearchScore } from '../frontend/src/care-search.ts';
assert.ok(careSearchScore('I would like help with everyday stress',['Stress and adjustment support'])>0);
assert.equal(careSearchScore('Grief and loss',['Stress and adjustment support']),0);
assert.ok(careSearchScore('I need someone to talk to',['Individual counseling'])>0);
assert.ok(careSearchScore('ስለ ሀዘን ድጋፍ እፈልጋለሁ',['የሀዘን ድጋፍ','ሀዘን'])>0);
assert.ok(careSearchScore('Ani gadda waa’ee deeggarsa barbaada',['Gadda fi deeggarsa'])>0);
assert.ok(careSearchScore('Mekdes Alemu',['Mekdes Alemu'])>careSearchScore('Mekdes Alemu',['Mekdes counseling']));
console.log('PASS: sentence search uses published terms, unrelated topics do not match, generic care query remains browsable, three-language tokens and exact clinician names.');
