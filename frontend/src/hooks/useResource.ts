import { useCallback, useEffect, useState } from "react";
export function useResource<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);
  const refresh = useCallback(async () => {
    setError(false);
    try {
      setData(await load());
    } catch {
      setError(true);
    }
  }, [load]);
  useEffect(() => {
    let active = true;
    load()
      .then((value) => {
        if (active) {
          setData(value);
          setError(false);
        }
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [load]);
  return { data, error, refresh };
}
