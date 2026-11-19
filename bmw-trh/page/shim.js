// Samostatná verzia dashboardu: dáta sú vložené v stránke (window.BMW_DATA), výpočty a kreslenie ako v dashboarde.
window.dash = (() => {
  const store = window.BMW_DATA || {};
  const calcs = new Map(); const memo = {};
  const draws = []; // [name, spec]
  const mounted = new WeakMap();
  const cbs = [];
  const get = (id) => {
    if (id in store) return store[id];
    if (id in memo) return memo[id];
    const c = calcs.get(id); if (!c) return null;
    memo[id] = c.fn(...c.inputs.map((i) => get(i) || []));
    return memo[id];
  };
  const run = (name, spec) => {
    document.querySelectorAll(`[data-draw="${name}"]`).forEach((el) => {
      try {
        if (typeof spec === 'function') { spec(el); return; }
        let made = mounted.get(el);
        if (made === undefined) { made = spec.mount ? spec.mount(el) : null; mounted.set(el, made); }
        if (spec.update) spec.update(el, made);
      } catch (e) { console.error('Kreslenie ' + name, e); }
    });
  };
  const api = {
    colors: ['#1f5fae', '#d0631f', '#7a8896', '#2f9d6a', '#8a5cc2', '#c23d6b', '#b38b12', '#3a8fb7'],
    calc(id, o) { calcs.set(id, o); },
    data(id) { const d = get(id); return {status: d ? 'ok' : 'missing', data: d || []}; },
    draw(name, spec) {
      if (spec === undefined) { draws.filter((d) => d[0] === name).forEach((d) => run(d[0], d[1])); return; }
      draws.push([name, spec]);
    },
    drawAll() { draws.forEach((d) => run(d[0], d[1])); },
    onData(fn) { cbs.push(fn); },
    params: () => ({}), setParams() {}, resetParams() {}, setLink() {}, refresh() {}, loader() {},
    start() {
      cbs.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
      api.drawAll();
      let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => api.drawAll(), 150); });
    },
  };
  return api;
})();
