import { reactive } from 'vue';
import { api } from './api';
import { session } from './session';
export const notificationState=reactive({unread:null});
let sequence=0;
export async function refreshUnread(){
 const generation=++sequence,id=session.user?.id;
 if(!id){notificationState.unread=null;return;}
 try{const result=await api('notifications/?unread=true&page_size=1');if(generation===sequence&&session.user?.id===id)notificationState.unread=result.count;}
 catch{if(generation===sequence)notificationState.unread=null;}
}
