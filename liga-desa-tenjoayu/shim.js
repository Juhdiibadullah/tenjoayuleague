/* shim.js — meniru google.script.run agar kode frontend lama jalan di GitHub Pages.
   Semua panggilan dikirim ke Cloudflare Worker (config.js -> API_URL). */
(function () {
  var cfg = window.LIGA_CONFIG || {};

  function baseUrl() { return location.origin + location.pathname.replace(/[^\/]*$/, ''); }

  // Alihkan tautan gaya Apps Script (?page=Admin dst.) ke file statis
  try {
    var page = new URLSearchParams(location.search).get('page');
    var peta = { Admin: 'admin.html', Tv: 'tv.html', Cetak: 'cetak.html', Daftar: 'daftar.html' };
    var file = location.pathname.split('/').pop();
    if (page && peta[page] && (file === '' || file === 'index.html')) location.replace(baseUrl() + peta[page]);
  } catch (e) {}

  function panggil(fn, args) {
    if (fn === 'urlApp') return Promise.resolve(baseUrl());
    var api = cfg.API_URL;
    if (!api || /GANTI/.test(api)) return Promise.reject(new Error('API_URL belum diisi di config.js'));
    return fetch(api, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ fn: fn, args: args })
    }).then(function (r) { return r.text(); }).then(function (t) {
      var j;
      try { j = JSON.parse(t); } catch (e) { throw new Error('Respons server tidak valid'); }
      if (!j || j.ok !== true) throw new Error((j && j.error) || 'Permintaan gagal');
      return j.data;
    });
  }

  function runner(ok, gagal) {
    return new Proxy({}, {
      get: function (_, nama) {
        if (nama === 'withSuccessHandler') return function (f) { return runner(f, gagal); };
        if (nama === 'withFailureHandler') return function (f) { return runner(ok, f); };
        if (nama === 'withUserObject') return function () { return runner(ok, gagal); };
        return function () {
          var args = Array.prototype.slice.call(arguments);
          panggil(String(nama), args).then(
            function (r) { if (ok) ok(r); },
            function (e) { if (gagal) gagal(e); else console.error(e); }
          );
        };
      }
    });
  }

  window.google = { script: { run: runner(null, null) } };
})();
