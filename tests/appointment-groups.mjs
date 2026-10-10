import assert from 'node:assert/strict';
import { appointmentGroups, appointmentDisplayGroups, appointmentsForView } from '../frontend/src/appointment-groups.ts';
const now=Date.parse('2026-10-09T12:00:00Z');
const make=(id, extras={})=>({id,state:'Booked',start:'2026-10-09T11:30:00Z',end:'2026-10-09T12:30:00Z',...extras});
const records=[make('ready'),make('ended',{call_state:'Ended',documentation_state:'Draft'}),make('complete',{state:'Completed',call_state:'Ended',documentation_state:'Finalized'}),make('expired-time',{end:'2026-10-09T11:50:00Z'}),make('cancelled',{state:'Cancelled',call_state:'Ended'}),make('active',{call_state:'Open'}),make('pending',{state:'PendingConfirmation'})];
for(const clinician of [false,true]){const groups=Object.fromEntries(appointmentGroups(records,clinician,now));assert.equal(Object.values(groups).flat().length,records.length);assert.equal(new Set(Object.values(groups).flat().map(x=>x.id)).size,records.length);assert.ok(groups.Upcoming.some(x=>x.id==='ready'));assert.ok(groups.Past.some(x=>x.id==='expired-time' && x.state==='Booked'));assert.ok(groups.Past.some(x=>x.id==='cancelled'));assert.ok(groups[clinician?'Needs action':'Past'].some(x=>x.id==='ended'));assert.ok(groups['In progress'].some(x=>x.id==='active'));assert.ok(!groups['Needs action'].some(x=>x.id==='complete'))}
console.log('PASS: single grouping, explicit terminal states, elapsed does not complete, patient has no clinician documentation task, current scheduled appointment remains visible.');

for (const clinician of [false, true]) {
  assert.deepEqual(appointmentsForView(records, 'upcoming', clinician, now).map(x=>x.id), ['ready','active']);
  assert.deepEqual(appointmentsForView(records, 'completed', clinician, now).map(x=>x.id), ['complete']);
  assert.deepEqual(appointmentsForView(records, 'cancelled', clinician, now).map(x=>x.id), ['cancelled']);
  assert.deepEqual(appointmentsForView(records, 'attention', clinician, now).map(x=>x.id), clinician ? ['ended','pending'] : ['pending']);
  assert.equal(appointmentsForView(records, 'all', clinician, now).length, records.length);
  assert.equal(records.find(x=>x.id==='expired-time').state, 'Booked');
}
console.log('PASS: view filters preserve elapsed/ended records and separate patient waiting from clinician documentation.');
const history=[make('previous-year',{state:'Completed',start:'2025-10-01T00:00:00Z'}),make('local-boundary',{state:'Completed',start:'2026-09-30T22:00:00Z',timezone:'Africa/Addis_Ababa'}),make('bad-zone',{state:'Completed',start:'2026-09-01T00:00:00Z',timezone:'Invalid/Legacy'}),make('missing-date',{state:'Completed',start:''})];
const months=Object.fromEntries(appointmentDisplayGroups(history,'completed',false,now,'en'));
assert.equal(months['October 2025'][0].id,'previous-year');
assert.equal(months['October 2026'][0].id,'local-boundary');
assert.equal(months['September 2026'][0].id,'bad-zone');
assert.equal(months.Past[0].id,'missing-date');
assert.deepEqual(history.map(x=>x.state),['Completed','Completed','Completed','Completed']);
console.log('PASS: historical month/year groups use booking timezone, retain incomplete legacy rows and preserve lifecycle.');
