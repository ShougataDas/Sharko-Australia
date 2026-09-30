interface VideoPreloaderProps {
  src: string;
}

// Silently buffers the next chapter's video in the background so the
// transition into it doesn't stall on a fresh download.
export default function VideoPreloader({ src }: VideoPreloaderProps) {
  return (
    <video
      src={src}
      preload="auto"
      muted
      playsInline
      style={{ display: "none" }}
      aria-hidden="true"
      tabIndex={-1}
    />
  );
}
