interface Props {
  digest: string[];
  yahooTrending?: string[];
}

export default function DiscussionDigest({ digest, yahooTrending = [] }: Props) {
  if (digest.length === 0) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6 mt-6">
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-lg font-semibold text-white">
          What Everyone&apos;s Saying
        </h2>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
          AI digest of all messages
        </span>
      </div>
      <div className="space-y-4 max-w-4xl">
        {digest.map((paragraph, i) => (
          <p key={i} className="text-sm text-gray-300 leading-relaxed">
            {paragraph}
          </p>
        ))}
      </div>
      {yahooTrending.length > 0 && (
        <div className="mt-5 pt-4 border-t border-gray-800">
          <span className="text-xs text-gray-500 uppercase tracking-wider mr-3">
            Also trending on Yahoo Finance
          </span>
          <div className="inline-flex gap-2 flex-wrap mt-2">
            {yahooTrending.slice(0, 10).map((t) => (
              <span
                key={t}
                className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-full"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
