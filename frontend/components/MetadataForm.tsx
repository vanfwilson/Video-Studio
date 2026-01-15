import React from "react";

export default function MetadataForm({
  title, description, tags, hashtags, thumbnailPrompt,
  onChange
}: {
  title: string;
  description: string;
  tags: string;
  hashtags: string;
  thumbnailPrompt: string;
  onChange: (patch: Partial<{ title: string; description: string; tags: string; hashtags: string; thumbnail_prompt: string }>) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium">Metadata</div>

      <div>
        <label className="text-xs text-slate-400">Title</label>
        <input
          className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
          value={title}
          onChange={(e) => onChange({ title: e.target.value })}
        />
      </div>

      <div>
        <label className="text-xs text-slate-400">Description</label>
        <textarea
          className="mt-1 w-full h-32 rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
          value={description}
          onChange={(e) => onChange({ description: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-400">Tags (comma-separated)</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
            value={tags}
            onChange={(e) => onChange({ tags: e.target.value })}
          />
        </div>
        <div>
          <label className="text-xs text-slate-400">Hashtags (space-separated)</label>
          <input
            className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
            value={hashtags}
            onChange={(e) => onChange({ hashtags: e.target.value })}
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-slate-400">Thumbnail prompt</label>
        <input
          className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
          value={thumbnailPrompt}
          onChange={(e) => onChange({ thumbnail_prompt: e.target.value })}
        />
      </div>
    </div>
  );
}
