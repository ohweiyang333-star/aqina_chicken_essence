import fs from 'node:fs';
import path from 'node:path';

const rootDir = process.cwd();
const imageUtilsPath = path.join(rootDir, 'src/lib/image-utils.ts');
const source = fs.readFileSync(imageUtilsPath, 'utf8');

const tokenEntries = new Map(
  [...source.matchAll(/'([^']+)':\s*'([^']+)'/gs)].map((match) => [
    match[1],
    match[2],
  ]),
);

const firebaseImageRefs = [
  ...source.matchAll(/getFirebase(V2)?Url\('([^']+)'\)/g),
].map((match) => (match[1] ? `V2/${match[2]}` : match[2]));

const uniqueImageRefs = [...new Set(firebaseImageRefs)];
const missingTokens = uniqueImageRefs.filter((objectPath) => !tokenEntries.has(objectPath));

if (missingTokens.length > 0) {
  console.error('[check-image-assets] Missing Firebase Storage download tokens:');
  for (const objectPath of missingTokens) {
    console.error(`- ${objectPath}`);
  }
  process.exit(1);
}

function getFirebaseUrl(objectPath) {
  const token = tokenEntries.get(objectPath);
  return `https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/${encodeURIComponent(objectPath)}?alt=media&token=${encodeURIComponent(token)}`;
}

async function fetchWithTimeout(url, timeoutMs = 15000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, {
      method: 'HEAD',
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function checkImage(objectPath) {
  const url = getFirebaseUrl(objectPath);
  let response;
  let lastError;

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      response = await fetchWithTimeout(url);
      if (response.ok) {
        break;
      }
    } catch (error) {
      lastError = error;
    }
  }

  if (!response?.ok) {
    return {
      objectPath,
      ok: false,
      reason: response
        ? `HTTP ${response.status} ${response.statusText}`
        : lastError?.message || 'Request failed',
    };
  }

  const contentType = response.headers.get('content-type') || '';

  if (!contentType.startsWith('image/')) {
    return {
      objectPath,
      ok: false,
      reason: `Unexpected content-type ${contentType || '(empty)'}`,
    };
  }

  return {
    objectPath,
    ok: true,
    reason: contentType,
  };
}

const results = await Promise.all(uniqueImageRefs.map(checkImage));
const failures = results.filter((result) => !result.ok);

for (const result of results) {
  const prefix = result.ok ? 'OK' : 'FAIL';
  console.log(`[check-image-assets] ${prefix} ${result.objectPath} (${result.reason})`);
}

if (failures.length > 0) {
  console.error('\n[check-image-assets] Firebase image connectivity check failed.');
  process.exit(1);
}

console.log(`\n[check-image-assets] Checked ${results.length} Firebase images.`);
