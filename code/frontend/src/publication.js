import { label, date } from './domain.js';
export const PUBLIC_PAGE_SIZE = 10;
export const publicCategories = ['FLOOD','EARTHQUAKE','FIRE','ACCIDENT'];
export const publicFields = [
  ['general_location','Lokasi','pin'], ['time_text','Waktu yang disebut','clock'],
  ['occurred_at','Waktu pasti','calendar'], ['general_impact','Dampak umum','alert'],
  ['summary','Ringkasan kejadian','reports'], ['handling_update','Perkembangan penanganan','clipboard'],
  ['published_at','Waktu publikasi','calendar'],
];
export const publicValue = (record, key) => !record?.[key] ? 'Belum tersedia' : ['occurred_at','published_at'].includes(key) ? date(record[key]) : String(record[key]);
export const publicTitle = item => item.general_location?.trim() || `${label(item.event_type)} · #${item.id.slice(0,8)}`;
export const publicationDate = value => value ? new Intl.DateTimeFormat('id-ID',{dateStyle:'medium'}).format(new Date(value)) : 'Belum tersedia';
export function publicListPath({q='',category='',page=1,pageSize=PUBLIC_PAGE_SIZE}={}) {
  const query = new URLSearchParams({page_size:String(pageSize),page:String(page)});
  if (q.trim()) query.set('q',q.trim());
  if (category) query.set('event_type',category);
  return 'public/reports/?' + query;
}
export function publicProjection(version, reportId) {
  return {id:reportId,...Object.fromEntries(['event_type','summary','general_location','time_text','occurred_at','general_impact','handling_update'].map(key=>[key,version.data[key]??null])),published_at:version.published_at};
}
