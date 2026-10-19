'use strict';

// Scope this preload to the pinned Pac-Man action only (via its NODE_OPTIONS).
// Its two analytics/leaderboard requests are unrelated to generating our graph.
const fetchGitHub = globalThis.fetch;
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');
let calendarHash;
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
  const days = weeks.flatMap(week => week.contributionDays).map(day => ({
    date: day.date, count: day.contributionCount, level: day.contributionLevel,
  })).sort((a, b) => a.date.localeCompare(b.date));
  const levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'];
  if (days.length < 365 || days.length > 367 || new Set(days.map(d => d.date)).size !== days.length ||
      days.some(d => !/^\d{4}-\d{2}-\d{2}$/.test(d.date) || !Number.isSafeInteger(d.count) || d.count < 0 ||
        !levels.includes(d.level) || ((d.count === 0) !== (d.level === 'NONE')))) {
    throw new Error('Pac-Man: invalid daily contribution data; refusing to publish');
  }
  const total = days.reduce((sum, day) => sum + day.count, 0);
  if (!total) {
    throw new Error('Pac-Man: GitHub returned a valid but all-zero calendar. Check Private contributions and commit eligibility; no synthetic path will be published.');
  }
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
