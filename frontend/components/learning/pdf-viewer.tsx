"use client";

import { useMemo } from "react";
import { Download, FileText } from "lucide-react";

interface PdfViewerProps {
  url: string;
  title?: string;
}

export function PdfViewer({ url, title }: PdfViewerProps) {
  // Use Google Docs viewer fallback if needed; here we rely on browser's native PDF viewer
  const embedUrl = useMemo(() => {
    const isAbsolute = /^https?:\/\//i.test(url);
    return isAbsolute ? url : url;
  }, [url]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between rounded-t-lg border border-b-0 bg-muted/40 px-3 py-2 text-sm">
        <span className="flex items-center gap-2 font-medium">
          <FileText className="h-4 w-4 text-red-500" />
          {title ?? "Document"}
        </span>
        <a
          href={embedUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-muted-foreground hover:text-primary"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Télécharger</span>
        </a>
      </div>
      <iframe
        src={embedUrl}
        title={title ?? "document"}
        className="-mt-2 h-[70vh] w-full rounded-b-lg border bg-white"
      />
    </div>
  );
}
