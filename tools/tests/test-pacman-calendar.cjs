'use strict';
// Synthetic unit fixtures only; never used by the generator or publisher.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../pacman-network.cjs'), 'utf8');
function guard(payload, status = 200) {
  const writes = [];
  const context = {
    module: { exports: {} }, URL, process: { env: {} }, console: { log() {} },
    fetch: async () => ({ ok: status === 200, status, clone: () => ({ json: async () => payload }) }),
    require: name => name === 'node:fs' ? { mkdirSync() {}, writeFileSync: (...args) => writes.push(args) } : require(name),
  };
  vm.runInNewContext(source, context);
  return { validate: context.module.exports.validateDays, fetch: context.fetch, writes };
}
function days(n = 368) {
  return Array.from({ length: n }, (_, i) => ({
    date: new Date(Date.UTC(2025, 9, 19 + i)).toISOString().slice(0, 10),
    count: i === 0 ? 1 : 0, level: i === 0 ? 'FIRST_QUARTILE' : 'NONE',
  }));
}
const validate = guard().validate;
for (const n of [365, 366, 367, 368, 369, 371]) test(`accept ${n} days`, () => assert.equal(validate(days(n)), 1));
const invalid = [
  ['short', () => days(364), /day count 364/], ['long', () => days(372), /day count 372/],
  ['not array', () => null, /must be an array/],
  ['duplicate', d => (d[1] = { ...d[0] }, d), /duplicate date/],
  ['gap', d => (d.splice(10, 1), d), /non-contiguous/],
  ['unordered', d => ([d[2], d[3]] = [d[3], d[2]], d), /non-contiguous/],
  ['impossible date', d => (d[0].date = '2025-02-30', d), /invalid date/],
  ['non ISO date', d => (d[0].date = '2025-2-03', d), /invalid date/],
  ['null day', d => (d[0] = null, d), /invalid day object/],
  ...[-1, 1.5, '1', true, null, 2 ** 53].map((v, i) => [`count ${i}`, d => (d[0].count = v, d), /invalid contribution count/]),
  ['level', d => (d[0].level = 'INVALID', d), /invalid contribution level/],
  ['mismatch', d => (d[0].level = 'NONE', d), /count\/level mismatch/],
  ['zero', d => (d[0] = { ...d[0], count: 0, level: 'NONE' }, d), /all-zero/],
  ['unsafe total', d => (d[0].count = Number.MAX_SAFE_INTEGER, d[1].count = 1, d[1].level = 'FIRST_QUARTILE', d), /total exceeds/],
];
for (const [name, change, message] of invalid) test(`reject ${name}`, () => assert.throws(() => validate(change(days())), message));
function payload(d) {
  const weeks = [];
  for (let i = 0; i < d.length; i += 7) weeks.push({ contributionDays: d.slice(i, i + 7).map(x => ({ date: x.date, contributionCount: x.count, contributionLevel: x.level })) });
  return { data: { user: { contributionsCollection: { contributionCalendar: { weeks } } } } };
}
const request = { method: 'POST', body: JSON.stringify({ variables: { login: 'lls144' } }) };
for (const n of [365, 367, 368, 371]) test(`network accepts ${n} real-shape days`, async () => {
  const g = guard(payload(days(n)));
  await g.fetch('https://api.github.com/graphql', request);
  assert.equal(JSON.parse(g.writes[0][1]).days.length, n);
});
for (const [name, data, status, match] of [
  ['HTTP', payload(days()), 403, /HTTP 403/],
  ['GraphQL', { errors: [{ message: 'do not log this' }] }, 200, /returned errors/],
  ['missing calendar', {}, 200, /no calendar/],
  ['bad days', payload(days(372)), 200, /week structure|day count/],
]) test(`network failure preserves output: ${name}`, async () => {
  const g = guard(data, status);
  await assert.rejects(g.fetch('https://api.github.com/graphql', request), match);
  assert.equal(g.writes.length, 0);
});
test('reject calendar changes between themes without replacing provenance', async () => {
  const data = payload(days()); const g = guard(data);
  await g.fetch('https://api.github.com/graphql', request);
  data.data.user.contributionsCollection.contributionCalendar.weeks[0].contributionDays[0].contributionCount = 2;
  await assert.rejects(g.fetch('https://api.github.com/graphql', request), /changed between themes/);
  assert.equal(g.writes.length, 1);
});
test('reject external requests and wrong identity', async () => {
  const g = guard(payload(days()));
  await assert.rejects(g.fetch('https://example.com', request), /outside/);
  await assert.rejects(g.fetch('https://api.github.com/graphql', { ...request, body: '{"variables":{"login":"other"}}' }), /expected the lls144/);
  assert.equal(g.writes.length, 0);
});
