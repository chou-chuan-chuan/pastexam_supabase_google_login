import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";
import { hasMeaningfulUploadMetadata, referenceFormValues } from "../assets/song-reference.js";
import { extractYouTubeVideoId, youtubeThumbnailUrl } from "../assets/youtube.js";

const app = (await readFile(new URL("../assets/app.js", import.meta.url), "utf8")).replace(/\r\n/g, "\n");
const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
const values = referenceFormValues({ status: "approved", title: "Lemon", artist: "米津玄師", album: "STRAY SHEEP",
  release_year: 2018, language: "日本語", genre: "Pop", youtube_video_id: "SX_ViT4Ra7k", song_tags: [{ tags: { id: "live" } }] }, [{ id: "live" }]);

function functionSource(name) {
  const start = app.indexOf(`function ${name}(`);
  return app.slice(start, app.indexOf("\n}\n", start) + 2);
}

function element(value = "") {
  const classes = new Set();
  return { value, textContent: "", focus() {},
    classList: { add: (name) => classes.add(name), remove: (name) => classes.delete(name),
      contains: (name) => classes.has(name), toggle: (name, force) => force ? classes.add(name) : classes.delete(name) } };
}

// Exercise the real form-application/reset/preview functions with isolated DOM controls.
function formHarness({ title = "", selectedTags = [], confirm = true } = {}) {
  const uploadMetadataInputs = Object.fromEntries(Object.keys(values).filter((key) => key !== "tag_ids").map((key) => [key, element()]));
  uploadMetadataInputs.title.value = title;
  const el = {
    uploadTags: { selected: selectedTags }, uploadNotes: element("My notes"), uploadPdf: { files: [{ name: "my-new.pdf" }] },
    uploadYoutube: uploadMetadataInputs.youtube_url, uploadYoutubeStatus: element(), uploadYoutubePreview: element(),
    uploadYoutubeThumbnail: element(), uploadYoutubeVideoId: element(), uploadReferenceInput: element(),
    clearUploadReference: element(), uploadReferenceStatus: element()
  };
  const state = { confirmations: 0, closed: 0 };
  const context = vm.createContext({ el, uploadMetadataInputs, approvedReferenceSongs: [{}], hasMeaningfulUploadMetadata,
    extractYouTubeVideoId, youtubeThumbnailUrl, selectedTagIds: (container) => container.selected,
    renderTagChoices: (container, ids) => { container.selected = ids; },
    closeUploadReferenceOptions: () => { state.closed++; },
    window: { confirm: () => { state.confirmations++; return confirm; } }
  });
  vm.runInContext(["updateYoutubePreview", "applyUploadReference", "resetUploadReference"].map(functionSource).join("\n"), context);
  return { el, state, inputs: uploadMetadataInputs, apply: () => context.applyUploadReference(values), clear: () => context.resetUploadReference() };
}

test("new-upload picker has combobox/listbox semantics, contextual label and six native datalists", () => {
  const upload = html.slice(html.indexOf('<form id="uploadForm"'), html.indexOf('<dialog id="editDialog"'));
  assert.match(upload, /新歌曲一律為待審核。[\s\S]*參考既有歌曲（選填）[\s\S]*歌曲名稱/);
  assert.match(upload, /role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="uploadReferenceOptions"/);
  assert.match(upload, /id="uploadReferenceOptions"[^>]*role="listbox"/);
  assert.match(upload, /autocomplete="off" placeholder="搜尋已通過歌曲名稱或歌手…"/);
  for (const name of ["Title", "Artist", "Album", "Year", "Language", "Genre"]) {
    assert.match(upload, new RegExp(`id="upload${name}" list="upload${name}Suggestions"`));
    assert.match(upload, new RegExp(`<datalist id="upload${name}Suggestions"`));
  }
  assert.doesNotMatch(html.slice(html.indexOf('<dialog id="editDialog"')), /uploadReference|Suggestions/);
});

test("selecting into empty reusable fields populates metadata/tags and updates YouTube validation/thumbnail", () => {
  const form = formHarness();
  const file = form.el.uploadPdf.files[0];
  form.apply();
  for (const [field, input] of Object.entries(form.inputs)) assert.equal(input.value, values[field]);
  assert.deepEqual(form.el.uploadTags.selected, ["live"]);
  assert.equal(form.state.confirmations, 0);
  assert.equal(form.el.uploadNotes.value, "My notes");
  assert.equal(form.el.uploadPdf.files[0], file);
  assert.equal(form.el.uploadYoutubeThumbnail.src, "https://i.ytimg.com/vi/SX_ViT4Ra7k/hqdefault.jpg");
  assert.equal(form.el.uploadYoutubeStatus.className, "field-success");
  assert.equal(form.el.uploadYoutubePreview.classList.contains("hidden"), false);
});

test("confirmation cancellation preserves typed fields, selected tags, notes and PDF", () => {
  const form = formHarness({ title: "My title", selectedTags: ["other"], confirm: false });
  form.apply();
  assert.equal(form.state.confirmations, 1);
  assert.equal(form.inputs.title.value, "My title");
  assert.equal(form.inputs.youtube_url.value, "");
  assert.deepEqual(form.el.uploadTags.selected, ["other"]);
  assert.equal(form.el.uploadNotes.value, "My notes");
  assert.equal(form.el.uploadPdf.files[0].name, "my-new.pdf");
});

test("confirmed replacement preserves PDF/notes; cleared reference leaves editable metadata/tags intact", () => {
  const form = formHarness({ title: "My title", confirm: true });
  form.apply();
  assert.equal(form.state.confirmations, 1);
  assert.equal(form.inputs.title.value, "Lemon");
  form.inputs.title.value = "My edited Lemon";
  form.el.uploadTags.selected = ["other"];
  form.clear();
  assert.equal(form.el.uploadReferenceInput.value, "");
  assert.equal(form.inputs.title.value, "My edited Lemon");
  assert.equal(form.inputs.artist.value, "米津玄師");
  assert.deepEqual(form.el.uploadTags.selected, ["other"]);
  assert.equal(form.el.uploadNotes.value, "My notes");
  assert.equal(form.el.uploadPdf.files[0].name, "my-new.pdf");
});

test("tag-only work also requires confirmation", () => {
  const form = formHarness({ selectedTags: ["other"], confirm: false });
  form.apply();
  assert.equal(form.state.confirmations, 1);
  assert.equal(form.inputs.title.value, "");
});

test("catalog reload rebuilds approved-only options and the original pending insert/PDF flow stays independent", () => {
  const load = functionSource("loadSongs");
  assert.match(load, /tags = tagsResult.data \|\| \[\];[\s\S]*rebuildUploadReferences\(\)/);
  assert.match(functionSource("rebuildUploadReferences"), /songs.filter\(\(song\) => song.status === "approved"\)/);
  const upload = functionSource("uploadSong");
  assert.match(upload, /crypto.randomUUID\(\)/);
  assert.match(upload, /\.upload\(path, file, \{ contentType: "application\/pdf", upsert: false \}\)/);
  assert.match(upload, /pendingSongPayload\(\{ \.\.\.values, pdf_path: path, original_filename: file.name \}, currentUser.id\)/);
  assert.match(upload, /from\("songs"\).insert\(payload\).select\("id"\).single\(\)/);
  assert.doesNotMatch(upload, /reference|approved_song_id|source_song_id|parent_song_id|lifecycle_id/i);
  const renderer = functionSource("renderUploadReferenceOptions");
  assert.doesNotMatch(renderer, /uploader|pdf_path|original_filename|\.id\)|innerHTML/);
  assert.match(renderer, /song.title[\s\S]*song.artist[\s\S]*song.album, song.release_year/);
});
