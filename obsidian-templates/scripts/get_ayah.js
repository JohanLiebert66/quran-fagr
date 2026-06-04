// get_ayah.js — Templater user script: يُرجِع نصّ الآية العثماني محليًّا.
// يقرأ obsidian-templates/data/quran-uthmani.json (مسارٌ من جذر الـ vault).
// يُستدعى: await tp.user.get_ayah(surah, ayah)
module.exports = async (surah, ayah) => {
  const path = "obsidian-templates/data/quran-uthmani.json";
  try {
    const raw = await app.vault.adapter.read(path);
    const data = JSON.parse(raw);
    const key = `${parseInt(surah, 10)}:${parseInt(ayah, 10)}`;
    return data[key] || "";
  } catch (e) {
    return "";
  }
};
