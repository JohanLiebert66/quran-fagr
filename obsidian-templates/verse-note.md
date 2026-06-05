<%*
// ملاحظة تدبّر آية — تُدرَج داخل ملف في surahs/verses/.
const s = await tp.system.prompt("رقم السورة (1-114)");
const a = await tp.system.prompt("رقم الآية");
const name = tp.user.surah_name(s);
let text = "";
try { text = await tp.user.get_ayah(s, a); } catch (e) {}
const tagsRaw = await tp.system.prompt("الوسوم (افصل بمسافة، ومتعدّد الكلمات بشرطة)", "");
const tags = (tagsRaw || "").split(/\s+/)
  .map(t => t.replace(/^#+/, "").trim()).filter(Boolean)
  .map(t => "#" + t).join(" · ");
const date = tp.date.now("YYYY-MM-DD");
const sNum = String(parseInt(s, 10)).padStart(3, "0");
const slug = (name || "").replace(/ /g, "-");
const meta = `*${date}${tags ? " · " + tags : ""} · [${name}:${a}](../quran/${sNum}-${slug}.md)*`;
tR += `## آية ${a}:\n> "${text}"\n\n${meta}\n`;
-%>
