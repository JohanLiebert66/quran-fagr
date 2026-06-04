<%*
// فائدة فجر موضوعية — تُدرَج داخل ملف في surahs/fajr/. الربط بآية اختياري.
const title = await tp.system.prompt("عنوان الفائدة");
const tagsRaw = await tp.system.prompt("الوسوم (افصل بمسافة، بلا #)", "");
const tags = (tagsRaw || "").split(/\s+/).filter(Boolean)
  .map(t => "#" + t.replace(/^#/, "")).join(" · ");
const date = tp.date.now("YYYY-MM-DD");
let link = "";
const s = await tp.system.prompt("رقم السورة للربط (اتركه فارغًا إن لم يلزم)", "");
if (s) {
  const a = await tp.system.prompt("رقم الآية (اختياري)", "");
  const name = tp.user.surah_name(s);
  const sNum = String(parseInt(s, 10)).padStart(3, "0");
  const slug = (name || "").replace(/ /g, "-");
  const ref = a ? `${name}:${a}` : name;
  link = ` · [${ref}](../quran/${sNum}-${slug}.md)`;
}
const meta = `*${date}${tags ? " · " + tags : ""}${link}*`;
tR += `## ${title}\n${meta}\n`;
-%>
<% tp.file.cursor() %>
