import { useCallback, useEffect, useState } from "react";
export function useResource<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [errorDetail, setErrorDetail] = useState<unknown>(null);
  const refresh = useCallback(async () => {
    setErrorDetail(null);
    try {
      setData(await load());
    } catch (error) {
      setErrorDetail(error);
    }
  }, [load]);
  useEffect(() => {
    let active = true;
    load()
      .then((value) => {
        if (active) {
          setData(value);
          setErrorDetail(null);
        }
      })
      .catch((error) => {
        if (active) setErrorDetail(error);
      });
    return () => {
      active = false;
    };
  }, [load]);
  return { data, error: errorDetail !== null, errorDetail, refresh };
}
