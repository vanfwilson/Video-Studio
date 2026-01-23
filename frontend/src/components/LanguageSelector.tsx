import React from "react";
import { ChevronDown, Check, Globe, Loader2 } from "lucide-react";
import { getSupportedLanguages, translateCaptions, type Language } from "../api/videoApi";
import { Button, useToast } from "./ui";

interface LanguageSelectorProps {
  videoId: number;
  existingLanguages?: string[];
  onTranslationComplete?: () => void;
  disabled?: boolean;
}

export default function LanguageSelector({
  videoId,
  existingLanguages = [],
  onTranslationComplete,
  disabled = false
}: LanguageSelectorProps) {
  const toast = useToast();
  const [open, setOpen] = React.useState(false);
  const [languages, setLanguages] = React.useState<Language[]>([]);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [translating, setTranslating] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Load available languages
  React.useEffect(() => {
    getSupportedLanguages()
      .then((res) => {
        setLanguages(res.languages);
        // Pre-select existing languages
        setSelected(new Set(existingLanguages));
      })
      .catch((e) => {
        console.error("Failed to load languages:", e);
      })
      .finally(() => setLoading(false));
  }, []);

  // Close dropdown on outside click
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const allSelected = selected.size === languages.length;
  const noneSelected = selected.size === 0;

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(languages.map((l) => l.code)));
    }
  };

  const toggleLanguage = (code: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(code)) {
      newSelected.delete(code);
    } else {
      newSelected.add(code);
    }
    setSelected(newSelected);
  };

  const handleTranslate = async () => {
    // Get languages to translate (exclude existing and source)
    const toTranslate = Array.from(selected).filter(
      (code) => !existingLanguages.includes(code) && code !== "en"
    );

    if (toTranslate.length === 0) {
      toast.push({ type: "info", message: "No new languages to translate" });
      return;
    }

    setTranslating(true);
    try {
      const result = await translateCaptions(videoId, toTranslate, "en");
      toast.push({
        type: "success",
        message: `Translated to ${result.languages_added.length} languages!`
      });
      onTranslationComplete?.();
    } catch (e: any) {
      toast.push({
        type: "error",
        message: e.response?.data?.detail || "Translation failed"
      });
    } finally {
      setTranslating(false);
      setOpen(false);
    }
  };

  const newLanguagesCount = Array.from(selected).filter(
    (code) => !existingLanguages.includes(code) && code !== "en"
  ).length;

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading languages...
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          disabled={disabled || translating}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg border text-sm
            ${disabled || translating
              ? "bg-slate-100 text-slate-400 cursor-not-allowed"
              : "bg-white hover:bg-slate-50 border-slate-300 text-slate-700"
            }
          `}
        >
          <Globe className="w-4 h-4" />
          <span>
            {selected.size === 0
              ? "Select Languages"
              : `${selected.size} language${selected.size !== 1 ? "s" : ""} selected`}
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </button>

        {newLanguagesCount > 0 && (
          <Button
            onClick={handleTranslate}
            busy={translating}
            disabled={disabled}
            className="text-sm py-1.5 px-3"
          >
            {translating ? "Translating..." : `Translate to ${newLanguagesCount} new`}
          </Button>
        )}
      </div>

      {open && (
        <div className="absolute z-50 mt-1 w-72 max-h-80 overflow-auto bg-white border border-slate-200 rounded-lg shadow-lg">
          {/* Select All Toggle */}
          <div className="sticky top-0 bg-white border-b border-slate-200 p-2">
            <label className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 cursor-pointer">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="font-medium text-sm">
                {allSelected ? "Deselect All" : "Select All"}
              </span>
              <span className="text-xs text-slate-400 ml-auto">
                ({languages.length} languages)
              </span>
            </label>
          </div>

          {/* Language List */}
          <div className="p-1">
            {languages.map((lang) => {
              const isExisting = existingLanguages.includes(lang.code);
              const isSelected = selected.has(lang.code);

              return (
                <label
                  key={lang.code}
                  className={`
                    flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer
                    ${isExisting ? "bg-green-50" : "hover:bg-slate-50"}
                  `}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleLanguage(lang.code)}
                    className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm flex-1">{lang.name}</span>
                  <span className="text-xs text-slate-400">{lang.code}</span>
                  {isExisting && (
                    <Check className="w-4 h-4 text-green-600" />
                  )}
                </label>
              );
            })}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-slate-50 border-t border-slate-200 p-2 text-xs text-slate-500">
            <div className="flex items-center justify-between">
              <span>
                {existingLanguages.length > 0 && (
                  <span className="text-green-600">
                    {existingLanguages.length} already translated
                  </span>
                )}
              </span>
              <span>
                {newLanguagesCount > 0 && `${newLanguagesCount} new to translate`}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
