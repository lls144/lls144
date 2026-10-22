'use strict';

// Scope this preload to the pinned Pac-Man action only (via its NODE_OPTIONS).
// Its two analytics/leaderboard requests are unrelated to generating our graph.
const fetchGitHub = globalThis.fetch;
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
let calendarHash;

// GitHub returns week buckets, not a fixed 365/366-day array. The pinned
// renderer has 53 columns: accept up to 53 * 7 real days, never pad or trim.
function validateDays(days) {
  const fail = message => { throw new Error(`Pac-Man: ${message}; refusing to publish`); };
  if (!Array.isArray(days)) fail('calendar days must be an array');
  if (days.length < 365 || days.length > 53 * 7) fail(`calendar day count ${days.length} outside 365..371 (53 weeks)`);
  const levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'];
  const seen = new Set();
  let previous, total = 0;
  for (const [index, day] of days.entries()) {
    if (!day || typeof day !== 'object') fail(`invalid day object at index ${index}`);
    if (typeof day.date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(day.date) || day.date.startsWith('0000')) fail(`invalid date at index ${index}`);
    const stamp = Date.parse(`${day.date}T00:00:00Z`);
    if (!Number.isFinite(stamp) || new Date(stamp).toISOString().slice(0, 10) !== day.date) fail(`invalid date at index ${index}`);
    if (seen.has(day.date)) fail(`duplicate date at index ${index}`);
    if (previous !== undefined && stamp - previous !== 86400000) fail(`non-contiguous or unordered dates at index ${index}`);
    if (!Number.isSafeInteger(day.count) || day.count < 0) fail(`invalid contribution count at index ${index}`);
    if (!levels.includes(day.level)) fail(`invalid contribution level at index ${index}`);
    if ((day.count === 0) !== (day.level === 'NONE')) fail(`count/level mismatch at index ${index}`);
    seen.add(day.date); previous = stamp; total += day.count;
  }
  if (!Number.isSafeInteger(total)) fail('contribution total exceeds safe integer range');
  if (!total) fail('valid but all-zero calendar; check Private contributions and commit eligibility; no synthetic path');
  return total;
}
module.exports = { validateDays };

globalThis.fetch = async function githubOnly(input, options = {}) {
  const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url);
  if (url.origin !== 'https://api.github.com' || url.pathname !== '/graphql' || url.search) {
    throw new Error('Pac-Man: blocked a request outside the GitHub contribution API');
  }
  const method = options.method || input.method || 'GET';
  const body = JSON.parse(options.body || '{}');
  if (method.toUpperCase() !== 'POST' || body.variables?.login !== 'lls144') {
    throw new Error('Pac-Man: expected the lls144 contribution calendar query');
  }
  const response = await fetchGitHub(input, { ...options, redirect: 'error' });
  if (!response.ok) throw new Error(`Pac-Man: GitHub HTTP ${response.status}; refusing to publish`);
  const json = await response.clone().json();
  const weeks = json.data?.user?.contributionsCollection?.contributionCalendar?.weeks;
  if (json.errors?.length || !Array.isArray(weeks)) {
    throw new Error('Pac-Man: GitHub returned errors or no calendar; refusing to publish');
  }
  if (weeks.length !== 53 || weeks.some(week => !Array.isArray(week?.contributionDays) ||
      week.contributionDays.length < 1 || week.contributionDays.length > 7)) {
    throw new Error('Pac-Man: invalid week structure; expected 53 weeks of 1..7 days; refusing to publish');
  }
  const days = weeks.flatMap(week => week.contributionDays).map(day => day && ({
    date: day.date, count: day.contributionCount, level: day.contributionLevel,
  }));
  const total = validateDays(days);
  const hash = crypto.createHash('sha256').update(JSON.stringify(days)).digest('hex');
  if (calendarHash && hash !== calendarHash) {
    throw new Error('Pac-Man: calendar changed between themes; retry for a consistent pair');
  }
  calendarHash = hash;
  const output = path.resolve('dist');
  fs.mkdirSync(output, { recursive: true });
  fs.writeFileSync(path.join(output, 'pacman-provenance.json'), JSON.stringify({
    username: 'lls144', source: 'https://api.github.com/graphql', retrievedUtc: new Date().toISOString(),
    generator: 'abozanona/pacman-contribution-graph@7332e1de7903ab780c3692a4127a59cc13872daa',
    workflowCommit: process.env.GITHUB_SHA || null,
    workflowRun: process.env.GITHUB_RUN_ID ? `https://github.com/lls144/lls144/actions/runs/${process.env.GITHUB_RUN_ID}` : null,
    from: days[0].date, to: days.at(-1).date, total, nonzeroDays: days.filter(d => d.count > 0).length,
    calendarSha256: hash, days,
  }, null, 2) + '\n');
  console.log(`GitHub calendar: ${days.length} days, ${total} contributions; SHA-256 ${hash}`);
  return response;
};
