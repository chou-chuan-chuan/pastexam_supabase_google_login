export function songTagObjects(song) {
  return (song?.song_tags || [])
    .map((relation) => relation?.tags)
    .filter(Boolean);
}

export function uploaderDisplayName(song) {
  return String(song?.uploader_display_name || "").trim()
    || String(song?.uploader_id || "").trim()
    || "—";
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

function compareCreatedAtDescending(left, right) {
  const createdDifference = Date.parse(right?.created_at || 0) - Date.parse(left?.created_at || 0);
  if (createdDifference) return createdDifference;
  return String(left?.id || "").localeCompare(String(right?.id || ""));
}

export function sortSongsForDisplay(songs, displayOrder = []) {
  const orderBySongId = new Map(
    (Array.isArray(displayOrder) ? displayOrder : [])
      .filter((row) => row?.song_id && Number.isFinite(Number(row.position)))
      .map((row) => [row.song_id, Number(row.position)])
  );
  const approvedWithOrder = [];
  const fallbackSongs = [];

  for (const song of Array.isArray(songs) ? songs : []) {
    if (song?.status === "approved" && orderBySongId.has(song.id)) approvedWithOrder.push(song);
    else fallbackSongs.push(song);
  }

  approvedWithOrder.sort((left, right) => {
    const positionDifference = orderBySongId.get(left.id) - orderBySongId.get(right.id);
    return positionDifference || compareCreatedAtDescending(left, right);
  });
  fallbackSongs.sort(compareCreatedAtDescending);
  return [...approvedWithOrder, ...fallbackSongs];
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
