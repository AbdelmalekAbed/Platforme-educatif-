"use client";

import { useMemo } from "react";

interface VideoPlayerProps {
  url: string;
  title?: string;
}

/**
 * Detects YouTube/Vimeo URLs and embeds them. Falls back to HTML5 video for direct files.
 */
function getYoutubeId(url: string): string | null {
  const patterns = [
    /youtube\.com\/watch\?v=([\w-]{11})/,
    /youtu\.be\/([\w-]{11})/,
    /youtube\.com\/embed\/([\w-]{11})/,
    /youtube\.com\/shorts\/([\w-]{11})/,
  ];
  for (const re of patterns) {
    const match = url.match(re);
    if (match) return match[1];
  }
  return null;
}

function getVimeoId(url: string): string | null {
  const match = url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  return match ? match[1] : null;
}

export function VideoPlayer({ url, title }: VideoPlayerProps) {
  const embed = useMemo(() => {
    const ytId = getYoutubeId(url);
    if (ytId) {
      return {
        kind: "iframe" as const,
        src: `https://www.youtube.com/embed/${ytId}?rel=0&modestbranding=1`,
      };
    }
    const vimeoId = getVimeoId(url);
    if (vimeoId) {
      return {
        kind: "iframe" as const,
        src: `https://player.vimeo.com/video/${vimeoId}`,
      };
    }
    return { kind: "html5" as const, src: url };
  }, [url]);

  return (
    <div className="aspect-video w-full overflow-hidden rounded-lg bg-black">
      {embed.kind === "iframe" ? (
        <iframe
          src={embed.src}
          title={title ?? "video"}
          className="h-full w-full"
          frameBorder={0}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      ) : (
        // eslint-disable-next-line jsx-a11y/media-has-caption
        <video src={embed.src} controls className="h-full w-full" />
      )}
    </div>
  );
}
