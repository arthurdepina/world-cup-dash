import { useEffect, useState } from "react";

// GitHub Pages serves under a subpath in prod; use import.meta.env.BASE_URL.
export function dataUrl(name) {
  return `${import.meta.env.BASE_URL}data/${name}`;
}

export function imgUrl(rel) {
  return `${import.meta.env.BASE_URL}${rel}`;
}

export function useJson(name) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    fetch(dataUrl(name))
      .then((r) => {
        if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => { if (!cancelled) setState({ data, error: null, loading: false }); })
      .catch((error) => { if (!cancelled) setState({ data: null, error, loading: false }); });
    return () => { cancelled = true; };
  }, [name]);

  return state;
}
