# Fonts

Self-hosted so the app renders identically offline, on a campus network and
behind a proxy, and so no visitor IP is sent to a third-party font CDN.

| Family | Files | Role | Source | License |
|---|---|---|---|---|
| Source Serif 4 | `source-serif-4-var-{latin,latin-ext}.woff2` | answer prose, document titles, brand | Adobe Source Serif, Google Fonts v14 | SIL OFL 1.1 (`OFL-SourceSerif4.txt`) |
| IBM Plex Sans | `ibm-plex-sans-var-{latin,latin-ext}.woff2` | interface: labels, buttons, dialogs | IBM Plex, Google Fonts | SIL OFL 1.1 (`OFL-IBMPlex.txt`) |
| IBM Plex Mono | `ibm-plex-mono-{400,500}-{latin,latin-ext}.woff2` | utility layer: citation numbers, retrieval ids, collection ids, scores, token counts | IBM Plex, Google Fonts | SIL OFL 1.1 (`OFL-IBMPlex.txt`) |

## Czech coverage

Czech needs both subsets: `á í é ú ý ó` and the typographic quotes live in
`latin`, while `ě š č ř ž ů ť ď ň` live in `latin-ext`. The `unicode-range`
descriptors in `styles.css` are the Google Fonts ranges verbatim, so a browser
fetches both for a Czech page and only `latin` for an English one. Shipping
`latin` alone is the classic way to get fallback-glyph confetti in Czech — do
not drop it.

## How these were produced

Downloaded from the Google Fonts `css2` API (which serves the upstream
binaries), then, for Source Serif 4 only:

    fonttools varLib.instancer <in>.woff2 opsz=14 wght=400:600 -o <tmp>.ttf
    pyftsubset <tmp>.ttf --unicodes=<the range in styles.css> --flavor=woff2 \
      --with-zopfli --layout-features=kern,liga,calt,ccmp,mark,mkmk,locl,onum,lnum,tnum,frac,sups,subs

Pinning the optical-size axis at 14 and clamping weight to 400–600 (the only
range the UI uses) takes that pair from 223 KB to 59 KB. IBM Plex Sans ships as
the upstream variable font — Google serves one file for every weight, so the
`400` and `600` downloads were byte-identical and only one copy is kept.

Total ~176 KB for all ten files; a Czech page loads ~144 KB of it, once.
