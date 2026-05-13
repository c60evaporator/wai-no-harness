import { useQuery } from '@tanstack/react-query'

export function useSensorImage(token: string | null) {
  return useQuery({
    queryKey: ['sensor-image', token],
    queryFn: async () => {
      const res = await fetch(`/api/v1/sensor-data/${token}/image`)
      if (!res.ok) throw new Error('image fetch failed')

      // AWS mode: response is {"url": "..."} → fetch from CloudFront
      if ((res.headers.get('content-type') ?? '').includes('application/json')) {
        const { url } = await res.json() as { url: string }
        const encodedUrl = url.replace(/\+/g, '%2B')  // CloudFront 経由で '+' がスペースとして解釈される問題への対処
        const imgRes = await fetch(encodedUrl)  // mode: 'cors'不要
        if (!imgRes.ok) throw new Error('CloudFront image fetch failed')
        return createImageBitmap(await imgRes.blob())
      }

      // Local mode: binary image stream
      return createImageBitmap(await res.blob())
    },
    enabled:   !!token,
    staleTime: Infinity,
    gcTime:    Infinity,
  })
}
