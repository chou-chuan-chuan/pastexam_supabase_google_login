export function songTagObjects(song) {
  return (song?.song_tags || [])
    .map((relation) => relation?.tags)
    .filter(Boolean);
}

export function matchesSong(song, filters = {}) {
  const query = String(filters.query || "").trim().toLocaleLowerCase();
  const tags = songTagObjects(song);
  const haystack = [
    song.title,
    song.artist,
    song.album,
    song.release_year,
    song.language,
    song.genre,
    song.notes,
    ...tags.flatMap((tag) => [tag.name, tag.slug])
  ].join(" ").toLocaleLowerCase();

  const selectedTags = Array.isArray(filters.tags) ? filters.tags.filter(Boolean) : [];
  const songTagKeys = new Set(tags.flatMap((tag) => [tag.id, tag.slug, tag.name]));

  return (!query || haystack.includes(query))
    && (!filters.language || song.language === filters.language)
    && (!filters.genre || song.genre === filters.genre)
    && (!filters.year || String(song.release_year ?? "") === String(filters.year))
    && selectedTags.every((tag) => songTagKeys.has(tag));
}

export function filterSongs(songs, filters = {}) {
  return (Array.isArray(songs) ? songs : []).filter((song) => matchesSong(song, filters));
}

export function pendingSongPayload(fields, uploaderId) {
  return {
    title: String(fields.title || "").trim(),
    artist: String(fields.artist || "").trim(),
    album: String(fields.album || "").trim() || null,
    release_year: fields.release_year ? Number(fields.release_year) : null,
    language: String(fields.language || "").trim() || null,
    genre: String(fields.genre || "").trim() || null,
    notes: String(fields.notes || "").trim() || null,
    youtube_video_id: fields.youtube_video_id,
    pdf_path: fields.pdf_path,
    original_filename: fields.original_filename,
    uploader_id: uploaderId,
    status: "pending"
  };
}
