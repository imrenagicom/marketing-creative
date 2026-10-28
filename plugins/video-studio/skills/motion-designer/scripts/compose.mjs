#!/usr/bin/env node
// Build one HyperFrames composition per canvas from timed shots and narration word timings.
// Usage: node compose.mjs <project-dir> [--gsap <local gsap.min.js>] [--force] [--only 9x16]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const GENERATOR = 'video-studio-compose-v1';
const GSAP_CDN = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js';
const SAFE = { // fraction of the canvas kept clear of platform UI
  '9x16': { top: 0.12, right: 0.07, bottom: 0.22, left: 0.07 },
  '16x9': { top: 0.08, right: 0.07, bottom: 0.1, left: 0.07 },
  '4x5': { top: 0.08, right: 0.07, bottom: 0.12, left: 0.07 },
  '1x1': { top: 0.08, right: 0.07, bottom: 0.1, left: 0.07 },
};
const DEFAULT_STYLE = {
  colors: { background: '#0F1115', surface: '#1A1D24', text: '#F4F1EA', accent: '#FF9F43', muted: '#8A8F98' },
  fonts: { display: 'Inter', body: 'Inter' }, radius: 28, motion: { ease: 'power3.out', entrance: 0.35 },
};

const ownFile = fileURLToPath(import.meta.url);
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const num = value => Number(value.toFixed(3));
const norm = token => token.normalize('NFKC').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
const stripTags = text => text.replace(/\[[^\]]*\]/g, ' ').replace(/\s+/g, ' ').trim();

export function parseArgs(argv) {
  const options = { root: null, gsap: null, force: false, only: null };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--force') options.force = true;
    else if (arg === '--gsap') options.gsap = argv[++i];
    else if (arg === '--only') options.only = argv[++i];
    else if (!options.root) options.root = arg;
    else throw new Error(`Unexpected argument ${arg}`);
  }
  if (!options.root) throw new Error('Usage: compose.mjs <project-dir> [--gsap file] [--force] [--only canvas]');
  return options;
}

// When each keyword (possibly several words) starts, matched inside its own line's words.
export function keywordCues(line, words) {
  const own = words.filter(word => word.line === line.id);
  const tokens = own.map(word => norm(word.text));
  return (line.keywords || []).map(keyword => {
    const parts = stripTags(keyword).split(' ').map(norm).filter(Boolean);
    for (let i = 0; i + parts.length <= tokens.length; i++) {
      if (parts.every((part, k) => tokens[i + k] === part)) {
        return { text: keyword, start: own[i].start, end: own[i + parts.length - 1].end };
      }
    }
    throw new Error(`Keyword "${keyword}" of ${line.id} is not in its narration timings; re-time or fix the script`);
  });
}

function lineSpans(words) {
  const spans = {};
  for (const word of words) {
    spans[word.line] ??= { start: word.start, end: word.end };
    spans[word.line].end = word.end;
  }
  return spans;
}

function sizes(format) {
  const { width: W, height: H } = format;
  const unit = Math.min(W, H);
  const wide = W / H > 1.2;
  return { W, H, unit, wide, safe: SAFE[format.id] };
}

function scene(shot, ctx) {
  const v = shot.visual || {};
  const id = shot.id;
  const tl = ctx.timeline;
  const at = t => num(Math.max(shot.start, t));
  const ease = JSON.stringify(ctx.style.motion?.ease || 'power3.out');
  const enter = ctx.style.motion?.entrance ?? 0.35;
  const lines = shot.lines.map(lineId => ctx.lines[lineId]);
  let html = '';
  switch (v.mode) {
    case 'kinetic': {
      // The spoken line, word by word; keywords take the accent colour on their words.
      const parts = [];
      for (const line of lines) {
        const keyTimes = new Set(keywordCues(line, ctx.words).flatMap(cue =>
          ctx.words.filter(w => w.line === line.id && w.start >= cue.start && w.end <= cue.end).map(w => w.start)));
        for (const [n, word] of ctx.words.filter(w => w.line === line.id).entries()) {
          const wid = `${id}-${line.id}-w${n}`;
          parts.push(`<span id="${wid}" class="word${keyTimes.has(word.start) ? ' key' : ''}">${esc(word.text)}</span>`);
          tl.push(`tl.fromTo("#${wid}",{opacity:0,y:${num(ctx.unit * 0.02)}},{opacity:1,y:0,duration:0.18,ease:${ease}},${at(word.start - 0.05)});`);
        }
        if (lines.length > 1) parts.push('<br>');
      }
      html = `<div class="kinetic">${parts.join(' ')}</div>`;
      break;
    }
    case 'title':
      html = `<div class="title-block"><h1 id="${id}-title">${esc(v.title)}</h1>${v.subtitle ? `<p id="${id}-sub">${esc(v.subtitle)}</p>` : ''}</div>`;
      tl.push(`tl.fromTo("#${id}-title",{opacity:0,scale:0.92},{opacity:1,scale:1,duration:${enter},ease:${ease}},${at(shot.start)});`);
      if (v.subtitle) tl.push(`tl.fromTo("#${id}-sub",{opacity:0,y:20},{opacity:1,y:0,duration:${enter},ease:${ease}},${at(shot.start + enter * 0.6)});`);
      break;
    case 'steps': {
      const items = v.items || [];
      html = `<ol class="steps">${items.map((item, n) => `<li id="${id}-i${n}"><span class="badge">${v.numbered === false ? '•' : n + 1}</span><span>${esc(item.text)}</span></li>`).join('')}</ol>`;
      items.forEach((item, n) => {
        const start = ctx.spans[item.line]?.start ?? shot.start;
        tl.push(`tl.fromTo("#${id}-i${n}",{opacity:0,x:${num(-ctx.unit * 0.04)}},{opacity:1,x:0,duration:${enter},ease:${ease}},${at(start - 0.1)});`);
        tl.push(`tl.to("#${id}-i${n} .badge",{backgroundColor:"var(--accent)",color:"var(--bg)",duration:0.2},${at(start - 0.1)});`);
        if (n > 0) tl.push(`tl.to("#${id}-i${n - 1}",{opacity:0.45,duration:0.25},${at(start - 0.1)});`);
      });
      break;
    }
    case 'ui-card': {
      const rows = v.rows || [];
      const hi = Number.isInteger(v.highlight) ? v.highlight : rows.length - 1;
      html = `<div class="card" id="${id}-card"><div class="card-label">${esc(v.label || 'Illustrative')}</div><div class="card-title">${esc(v.title)}</div>${rows.map((row, n) => `<div class="row" id="${id}-r${n}">${esc(row)}</div>`).join('')}<div class="cursor" id="${id}-cursor"></div></div>`;
      const span = shot.end - shot.start;
      tl.push(`tl.fromTo("#${id}-card",{opacity:0,y:${num(ctx.unit * 0.05)}},{opacity:1,y:0,duration:${enter},ease:${ease}},${at(shot.start)});`);
      tl.push(`tl.fromTo("#${id}-cursor",{left:"85%",top:"95%"},{left:"70%",top:"${num(30 + (hi + 1) * (60 / Math.max(rows.length, 1)))}%",duration:${num(span * 0.3)},ease:"power2.inOut"},${at(shot.start + span * 0.15)});`);
      if (rows.length) tl.push(`tl.to("#${id}-r${hi}",{backgroundColor:"var(--accent)",color:"var(--bg)",duration:0.2},${at(shot.start + span * 0.45)});`);
      break;
    }
    case 'stat': {
      const from = Number(v.from ?? 0), to = Number(v.value);
      if (!Number.isFinite(to)) throw new Error(`${id} stat value must be a number`);
      const span = ctx.spans[shot.lines[0]] || { start: shot.start, end: shot.end };
      const locale = ctx.language === 'id' ? 'id-ID' : 'en-US';
      const decimals = (String(v.value).split('.')[1] || '').length;
      html = `<div class="stat"><div class="stat-value">${esc(v.prefix || '')}<span id="${id}-n">${esc(from.toLocaleString(locale))}</span>${esc(v.suffix || '')}</div><div class="stat-label" id="${id}-label">${esc(v.label)}</div></div>`;
      tl.push(`(()=>{const c={v:${from}};tl.fromTo(c,{v:${from}},{v:${to},duration:${num(Math.max(0.4, (span.end - span.start) * 0.6))},ease:"power2.out",onUpdate:()=>{document.getElementById("${id}-n").textContent=c.v.toLocaleString(${JSON.stringify(locale)},{minimumFractionDigits:${decimals},maximumFractionDigits:${decimals}});}},${at(span.start)});})();`);
      tl.push(`tl.fromTo("#${id}-label",{opacity:0},{opacity:1,duration:${enter}},${at(span.start + 0.2)});`);
      break;
    }
    case 'image': {
      const asset = ctx.copyAsset(v.asset);
      html = `<figure class="image"><img id="${id}-img" src="${esc(asset)}" alt="${esc(v.caption || 'Supplied image')}" style="object-fit:${v.fit === 'cover' ? 'cover' : 'contain'}">${v.caption ? `<figcaption>${esc(v.caption)}</figcaption>` : ''}</figure>`;
      tl.push(`tl.fromTo("#${id}-img",{opacity:0,scale:1.04},{opacity:1,scale:1,duration:${enter * 1.4},ease:${ease}},${at(shot.start)});`);
      break;
    }
    case 'end-card':
      html = `<div class="end-card"><h1 id="${id}-title">${esc(v.title)}</h1>${v.subtitle ? `<p id="${id}-sub">${esc(v.subtitle)}</p>` : ''}</div>`;
      tl.push(`tl.fromTo("#${id}-title",{opacity:0,scale:0.85},{opacity:1,scale:1,duration:${enter * 1.3},ease:"back.out(1.6)"},${at(shot.start)});`);
      if (v.subtitle) tl.push(`tl.fromTo("#${id}-sub",{opacity:0,y:16},{opacity:1,y:0,duration:${enter},ease:${ease}},${at(shot.start + enter)});`);
      break;
    default:
      throw new Error(`${id}: unsupported visual mode ${v.mode}; add a project-local generator for custom scenes`);
  }
  // Kinetic keywords for the shot's lines (the kinetic mode already shows every word).
  let keys = '';
  if (v.mode !== 'kinetic' && v.keywords !== false) {
    const cues = lines.flatMap(line => keywordCues(line, ctx.words).map(cue => ({ ...cue, line: line.id })));
    keys = cues.map((cue, n) => `<span class="key-chip" id="${id}-k${n}">${esc(cue.text)}</span>`).join('');
    cues.forEach((cue, n) => {
      const lineEnd = ctx.spans[cue.line].end;
      tl.push(`tl.fromTo("#${id}-k${n}",{opacity:0,y:${num(ctx.unit * 0.015)}},{opacity:1,y:0,duration:0.2,ease:${ease}},${at(cue.start - 0.05)});`);
      tl.push(`tl.to("#${id}-k${n}",{opacity:0,duration:0.2},${num(Math.min(shot.end - 0.05, lineEnd + 0.25))});`);
    });
  }
  // Transition into the shot.
  let wipe = '';
  if (shot.transition === 'wipe') {
    wipe = `<div class="wipe" id="${id}-wipe"></div>`;
    tl.push(`tl.fromTo("#${id}-wipe",{xPercent:-101},{xPercent:101,duration:0.45,ease:"power2.inOut"},${num(shot.start)});`);
  } else if (shot.transition === 'fade') {
    tl.push(`tl.fromTo("#${id}-scene",{opacity:0},{opacity:1,duration:0.4},${num(shot.start)});`);
  } else if (shot.transition === 'push') {
    tl.push(`tl.fromTo("#${id}-scene",{xPercent:8},{xPercent:0,duration:0.35,ease:${ease}},${num(shot.start)});`);
  }
  return `<section id="${id}" class="clip" data-start="${num(shot.start)}" data-duration="${num(shot.end - shot.start)}" data-track-index="2">
<div class="scene mode-${v.mode}" id="${id}-scene">${html}<div class="keys">${keys}</div></div>${wipe}</section>`;
}

export function documentFor({ project, format, shots, script, words, style, audio, gsapSrc, copyAsset }) {
  const s = sizes(format);
  const lines = Object.fromEntries(script.lines.map(line => [line.id, line]));
  const ctx = { timeline: [], unit: s.unit, style, lines, words: words.words, spans: lineSpans(words.words),
    language: project.language, copyAsset };
  const duration = num(shots.shots.at(-1).end);
  const body = shots.shots.map(shot => scene(shot, ctx)).join('\n');
  const c = { ...DEFAULT_STYLE.colors, ...(style.colors || {}) };
  for (const [key, value] of Object.entries(c)) {
    if (!/^#[0-9A-Fa-f]{6}$/.test(value)) throw new Error(`style.colors.${key} must be #RRGGBB`);
  }
  const font = name => `${JSON.stringify(name || 'Inter')},system-ui,-apple-system,"Segoe UI",sans-serif`;
  const display = font(style.fonts?.display), bodyFont = font(style.fonts?.body);
  const u = s.unit, r = style.radius ?? 28;
  const pad = s.safe;
  return `<!doctype html>
<html lang="${esc(project.language || 'en')}"><head><meta charset="utf-8"><meta name="viewport" content="width=${s.W},height=${s.H}">
<title>${esc(project.title)} ${esc(format.id)}</title>
<script src="${esc(gsapSrc)}"></script>
<style>
/* Initial hidden states come from the GSAP timeline (fromTo renders its start state), not CSS. */
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:${c.background}}
#root{position:relative;width:100%;height:100%;overflow:hidden;--bg:${c.background};--surface:${c.surface};--text:${c.text};--accent:${c.accent};--muted:${c.muted};color:var(--text);font-family:${bodyFont}}
.glow{position:absolute;width:${num(u * 1.2)}px;height:${num(u * 1.2)}px;border-radius:50%;background:radial-gradient(circle,${c.accent}22 0%,transparent 65%);left:${s.wide ? '60%' : '-20%'};top:${s.wide ? '-30%' : '45%'}}
.clip{position:absolute;inset:0;overflow:hidden}
.scene{position:absolute;inset:${pad.top * 100}% ${pad.right * 100}% ${pad.bottom * 100}% ${pad.left * 100}%;display:flex;flex-direction:column;justify-content:center;align-items:${s.wide ? 'flex-start' : 'center'};gap:${num(u * 0.04)}px;text-align:${s.wide ? 'left' : 'center'}}
.kinetic{font-family:${display};font-weight:800;font-size:${num(u * (s.wide ? 0.085 : 0.105))}px;line-height:1.08;letter-spacing:-0.02em;max-width:${s.wide ? '75%' : '100%'}}
.word{display:inline-block}.word.key{color:var(--accent)}
.title-block h1,.end-card h1{font-family:${display};font-weight:850;margin:0;font-size:${num(u * 0.11)}px;line-height:1.02;letter-spacing:-0.03em}
.title-block p,.end-card p{margin:0;font-size:${num(u * 0.045)}px;color:var(--muted)}
.end-card h1{color:var(--accent)}
.steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:${num(u * 0.03)}px;width:${s.wide ? '70%' : '100%'}}
.steps li{display:flex;align-items:center;gap:${num(u * 0.03)}px;padding:${num(u * 0.025)}px ${num(u * 0.035)}px;border-radius:${r}px;background:var(--surface);font-size:${num(u * 0.05)}px;font-weight:700;text-align:left}
.badge{flex:none;display:grid;place-items:center;width:${num(u * 0.08)}px;height:${num(u * 0.08)}px;border-radius:50%;border:3px solid var(--accent);color:var(--accent);font-weight:800}
.card{position:relative;width:${s.wide ? '60%' : '100%'};padding:${num(u * 0.04)}px;border-radius:${r}px;background:var(--surface);text-align:left}
.card-label{font-size:${num(u * 0.022)}px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.card-title{font-size:${num(u * 0.05)}px;font-weight:800;margin:${num(u * 0.015)}px 0 ${num(u * 0.03)}px}
.row{padding:${num(u * 0.022)}px ${num(u * 0.03)}px;margin-top:${num(u * 0.015)}px;border-radius:${num(r * 0.6)}px;background:${c.background};font-size:${num(u * 0.038)}px}
.cursor{position:absolute;width:${num(u * 0.035)}px;height:${num(u * 0.035)}px;background:var(--text);clip-path:polygon(0 0,100% 62%,55% 62%,38% 100%)}
.stat-value{font-family:${display};font-weight:850;font-size:${num(u * 0.2)}px;line-height:1;color:var(--accent);font-variant-numeric:tabular-nums}
.stat-label{font-size:${num(u * 0.05)}px;color:var(--muted)}
.image{margin:0;width:100%;flex:1;min-height:0;display:flex;flex-direction:column;gap:${num(u * 0.02)}px}.image img{width:100%;flex:1;min-height:0;border-radius:${r}px}
.image figcaption{font-size:${num(u * 0.035)}px;color:var(--muted)}
.keys{display:flex;flex-wrap:wrap;gap:${num(u * 0.02)}px;justify-content:${s.wide ? 'flex-start' : 'center'};min-height:${num(u * 0.09)}px}
.key-chip{font-family:${display};font-weight:800;font-size:${num(u * 0.055)}px;padding:${num(u * 0.012)}px ${num(u * 0.03)}px;border-radius:999px;background:var(--accent);color:var(--bg)}
.wipe{position:absolute;inset:0;background:var(--accent)}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="${s.W}" data-height="${s.H}" data-duration="${duration}">
<div class="glow"></div>
${body}
${audio ? `<audio id="narration" src="${esc(audio)}" data-start="0" data-duration="${num(words.duration)}" data-track-index="10" data-volume="1"></audio>` : ''}
</div>
<script>
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
${ctx.timeline.join('\n')}
window.__videoStudio = ${JSON.stringify({ generator: GENERATOR, canvas: format.id, duration, shots: shots.shots.map(s2 => ({ id: s2.id, start: s2.start, end: s2.end })) })};
window.__timelines["main"] = tl;
</script></body></html>
`;
}

function safeJoin(root, relative) {
  if (path.isAbsolute(relative)) throw new Error(`Expected a project-relative path: ${relative}`);
  const result = path.resolve(root, relative);
  if (!result.startsWith(root + path.sep)) throw new Error(`Path escapes the project: ${relative}`);
  return result;
}

export function build(options) {
  const root = fs.realpathSync(path.resolve(options.root));
  execFileSync('python3', [path.resolve(path.dirname(ownFile), '../../studio-producer/scripts/studio.py'), 'validate', root], { stdio: 'pipe' });
  const load = name => readJson(path.join(root, name));
  const project = load('project.json');
  const script = load('script/script.json');
  const words = load('voice/words.json');
  const shots = load('shots/shots.json');
  const style = fs.existsSync(path.join(root, 'style.json')) ? load('style.json') : DEFAULT_STYLE;
  if (!shots.shots.every(shot => typeof shot.start === 'number')) throw new Error('Shots are not timed; run shots.py time first');
  if (shots.timed_against && shots.timed_against.duration !== words.duration) {
    throw new Error('Shots were timed against a different narration take; re-run shots.py time');
  }
  if (shots.shots.some(shot => shot.kind !== 'graphic')) throw new Error('Camera shots need footage; this generator builds graphic shots only');
  if (options.gsap && !fs.statSync(options.gsap).isFile()) throw new Error('--gsap needs a local file');
  const formats = project.formats.filter(format => !options.only || format.id === options.only);
  if (!formats.length) throw new Error(`No canvas ${options.only} in project.json`);
  const inputHashes = Object.fromEntries(['project.json', 'script/script.json', 'voice/words.json', 'shots/shots.json', 'style.json']
    .filter(name => fs.existsSync(path.join(root, name))).map(name => [name, sha(fs.readFileSync(path.join(root, name)))]));

  // Refuse to overwrite hand edits before writing anything.
  for (const format of formats) {
    const dest = safeJoin(root, path.join('compositions', format.id));
    const manifest = path.join(dest, 'build.json');
    if (!fs.existsSync(dest)) continue;
    if (!fs.existsSync(manifest)) {
      if (fs.existsSync(path.join(dest, 'index.html')) && !options.force) throw new Error(`compositions/${format.id} has untracked files; preserve edits, then use --force`);
      continue;
    }
    const prior = readJson(manifest);
    for (const [relative, expected] of Object.entries(prior.generatedHashes || {})) {
      const file = safeJoin(dest, relative);
      if (fs.existsSync(file) && sha(fs.readFileSync(file)) !== expected && !options.force) {
        throw new Error(`compositions/${format.id}/${relative} was edited after generation; reconcile it, then use --force`);
      }
    }
  }

  const results = [];
  for (const format of formats) {
    const dest = safeJoin(root, path.join('compositions', format.id));
    fs.mkdirSync(dest, { recursive: true });
    const generated = [];
    const copy = (source, relative) => {
      const target = safeJoin(dest, relative);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(source, target);
      generated.push(relative);
      return relative;
    };
    const copyAsset = relative => copy(safeJoin(root, relative), path.join('assets', relative));
    const audioSource = safeJoin(root, words.audio);
    const audio = fs.existsSync(audioSource) ? copy(audioSource, path.join('assets', words.audio)) : null;
    const gsapSrc = options.gsap ? copy(path.resolve(options.gsap), 'assets/runtime/gsap.min.js') : GSAP_CDN;
    const html = documentFor({ project, format, shots, script, words, style, audio, gsapSrc, copyAsset });
    fs.writeFileSync(path.join(dest, 'index.html'), html);
    generated.push('index.html');
    const manifest = { schemaVersion: 1, generator: GENERATOR, generatorSha256: sha(fs.readFileSync(ownFile)), canvas: format.id,
      width: format.width, height: format.height, duration: num(shots.shots.at(-1).end), localGsap: Boolean(options.gsap),
      narration: audio ? words.audio : null, inputHashes,
      generatedHashes: Object.fromEntries(generated.map(file => [file, sha(fs.readFileSync(path.join(dest, file)))])) };
    fs.writeFileSync(path.join(dest, 'build.json'), JSON.stringify(manifest, null, 2) + '\n');
    results.push({ canvas: format.id, path: path.relative(root, dest), duration: manifest.duration, narration: Boolean(audio), localGsap: manifest.localGsap });
  }
  return results;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === ownFile) {
  try {
    console.log(JSON.stringify(build(parseArgs(process.argv.slice(2))), null, 2));
  } catch (error) {
    process.stderr.write(`compose: ${error.stderr?.toString().trim() || error.message}\n`);
    process.exitCode = 1;
  }
}
