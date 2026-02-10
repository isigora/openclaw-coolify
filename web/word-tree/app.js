const inputEl = document.getElementById('wordInput');
const searchBtn = document.getElementById('searchBtn');
const detailEl = document.getElementById('detail');
const svg = d3.select('#treemap');
const width = 1000;
const height = 560;

let nodeByName = new Map();
let rectByName = new Map();

function toD3Node(name, node) {
  const children = Object.entries(node.children || {}).map(([k, v]) => toD3Node(k, v));
  return {
    name,
    label: node.label || '',
    pos: node.pos || '',
    aliases: node.aliases || [],
    related: node.related || [],
    examples: node.examples || [],
    children,
    value: children.length ? undefined : 1,
  };
}

function showDetail(data) {
  const local = data.local_match;
  const ctx = data.local_context;
  const cedict = data.cedict || [];

  detailEl.innerHTML = '';
  const blocks = [];

  if (local) {
    const node = local.node;
    blocks.push(`<p><strong>경로/路径:</strong> ${local.path.join(' > ')}</p>`);
    blocks.push(`<p><strong>词性:</strong> ${node.pos || '未标注'}</p>`);
    blocks.push(`<p><strong>说明:</strong> ${node.label || ''}</p>`);
    blocks.push(`<p><strong>别名:</strong> ${(node.aliases || []).join('、') || '-'}</p>`);
    blocks.push(`<p><strong>相关词:</strong> ${(node.related || []).join('、') || '-'}</p>`);

    if ((node.examples || []).length) {
      blocks.push('<p><strong>例句:</strong></p><ul>' + node.examples.map((e) => `<li>${e}</li>`).join('') + '</ul>');
    }

    if (ctx) {
      blocks.push(`<p><strong>주변/周边:</strong></p>`);
      blocks.push(`<p>Parent: ${ctx.parent || '-'}</p>`);
      blocks.push(`<p>Siblings: ${(ctx.siblings || []).join('、') || '-'}</p>`);
      blocks.push(`<p>Children: ${(ctx.children || []).join('、') || '-'}</p>`);
    }
  } else {
    blocks.push('<p>로컬 트리에서 직접 매치되는 항목이 없습니다.</p>');
  }

  if (cedict.length) {
    blocks.push('<h3>CC-CEDICT</h3>');
    blocks.push('<ul>' + cedict.slice(0, 5).map((x) => `<li>${x.simplified} / ${x.traditional} [${x.pinyin}] - ${x.definitions}</li>`).join('') + '</ul>');
  }

  if (data.wiktionary) {
    blocks.push(`<h3>Wiktionary</h3><p>${data.wiktionary}</p>`);
  }
  if (data.wikipedia) {
    blocks.push(`<h3>Wikipedia</h3><p>${data.wikipedia}</p>`);
  }

  detailEl.innerHTML = blocks.join('');
}

function clearHighlight() {
  d3.selectAll('.node-rect').classed('highlight', false);
}

function highlightWord(word) {
  clearHighlight();
  const rect = rectByName.get(word);
  if (rect) {
    rect.classed('highlight', true);
  }
}

async function lookupWord(word) {
  const res = await fetch(`/api/lookup?word=${encodeURIComponent(word)}`);
  const data = await res.json();
  showDetail(data);
  if (data.local_match) {
    const leaf = data.local_match.path[data.local_match.path.length - 1];
    highlightWord(leaf);
  }
}

function renderTreemap(tree) {
  const [rootName, rootNode] = Object.entries(tree)[0];
  const data = toD3Node(rootName, rootNode);

  const root = d3.hierarchy(data).sum((d) => d.value || 0.5).sort((a, b) => b.value - a.value);
  d3.treemap().size([width, height]).padding(2)(root);

  const color = d3.scaleOrdinal(d3.schemeTableau10);

  const g = svg.selectAll('g.node').data(root.descendants()).enter().append('g').attr('class', 'node');

  const rects = g
    .append('rect')
    .attr('class', 'node-rect')
    .attr('x', (d) => d.x0)
    .attr('y', (d) => d.y0)
    .attr('width', (d) => Math.max(0, d.x1 - d.x0))
    .attr('height', (d) => Math.max(0, d.y1 - d.y0))
    .attr('fill', (d) => color(d.depth))
    .on('click', (_, d) => {
      const name = d.data.name;
      inputEl.value = name;
      lookupWord(name);
    });

  g
    .append('text')
    .attr('class', 'node-label')
    .attr('x', (d) => d.x0 + 4)
    .attr('y', (d) => d.y0 + 14)
    .text((d) => d.data.name)
    .style('display', (d) => (d.x1 - d.x0 > 42 && d.y1 - d.y0 > 20 ? 'block' : 'none'));

  root.descendants().forEach((d, idx) => {
    nodeByName.set(d.data.name, d);
    rectByName.set(d.data.name, d3.select(rects.nodes()[idx]));
  });
}

async function boot() {
  const tree = await fetch('/api/tree').then((r) => r.json());
  renderTreemap(tree);
}

searchBtn.addEventListener('click', () => {
  const word = inputEl.value.trim();
  if (word) lookupWord(word);
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const word = inputEl.value.trim();
    if (word) lookupWord(word);
  }
});

boot();
