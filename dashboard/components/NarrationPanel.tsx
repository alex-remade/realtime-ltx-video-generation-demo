"use client";

import React from "react";

interface NarrationEntry {
  timestamp: number;
  generation_id: number;
  character: string;
  dialogue: string;
  audio_url: string;
}

interface NarrationPanelProps {
  narrationHistory: NarrationEntry[];
  ttsStatus?: any;
}

const CHARACTER_EMOJIS: { [key: string]: string } = {
  spongebob: "🧽",
  narrator: "📖",
  mysterious: "🎭",
};

const CHARACTER_COLORS: { [key: string]: string } = {
  spongebob: "bg-yellow-500/20 border-yellow-500/40 text-yellow-200",
  narrator: "bg-blue-500/20 border-blue-500/40 text-blue-200",
  mysterious: "bg-purple-500/20 border-purple-500/40 text-purple-200",
};

export function NarrationPanel({ narrationHistory, ttsStatus }: NarrationPanelProps) {
  const sortedHistory = [...narrationHistory].sort((a, b) => b.generation_id - a.generation_id);

  return (
    <div className="bg-gradient-to-br from-gray-800/90 to-gray-900/90 rounded-xl p-6 border border-gray-700/50 shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="text-2xl">🎤</span>
          Character Narration
        </h3>
        {ttsStatus && (
          <div className="text-xs text-gray-400">
            <div>TTS Generations: {ttsStatus.total_generations || 0}</div>
            <div>Avg Time: {ttsStatus.avg_generation_time || 0}s</div>
          </div>
        )}
      </div>

      {sortedHistory.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🎬</div>
          <div>No narrations yet</div>
          <div className="text-sm mt-1">Character dialogue will appear here</div>
        </div>
      ) : (
        <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
          {sortedHistory.map((entry, idx) => {
            const characterColor =
              CHARACTER_COLORS[entry.character] || "bg-gray-500/20 border-gray-500/40 text-gray-200";
            const characterEmoji = CHARACTER_EMOJIS[entry.character] || "🎭";

            return (
              <div
                key={`${entry.generation_id}-${idx}`}
                className={`p-4 rounded-lg border ${characterColor} backdrop-blur-sm`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{characterEmoji}</span>
                    <div>
                      <div className="font-bold capitalize">{entry.character}</div>
                      <div className="text-xs opacity-60">Scene #{entry.generation_id}</div>
                    </div>
                  </div>
                  {entry.audio_url && (
                    <button
                      onClick={() => {
                        const audio = new Audio(entry.audio_url);
                        audio.play().catch((err) => console.error("Playback error:", err));
                      }}
                      className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded-md text-xs font-medium transition-colors"
                      title="Play audio"
                    >
                      ▶️ Play
                    </button>
                  )}
                </div>
                <div className="text-sm leading-relaxed italic">
                  &quot;{entry.dialogue}&quot;
                </div>
                {entry.audio_url && (
                  <div className="mt-2 pt-2 border-t border-current/20">
                    <audio
                      src={entry.audio_url}
                      controls
                      className="w-full h-8"
                      style={{ maxHeight: "32px" }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

