<script setup>
import { ref, watch } from 'vue';
import AppIcon from './AppIcon.vue';

defineOptions({inheritAttrs:false});
const props=defineProps({
  modelValue:{type:String,default:''},
  id:{type:String,required:true},
  disabled:Boolean,
  toggleLabel:{type:String,default:'kata sandi'},
});
const emit=defineEmits(['update:modelValue']);
const visible=ref(false);
watch(()=>props.modelValue,value=>{if(!value)visible.value=false;});
watch(()=>props.disabled,value=>{if(value)visible.value=false;});
</script>
<template>
  <div class="auth-password-input">
    <input :id="id" v-bind="$attrs" :type="visible?'text':'password'" :value="modelValue"
      :disabled="disabled" autocapitalize="off" spellcheck="false"
      @input="emit('update:modelValue',$event.target.value)">
    <button class="quiet auth-password-toggle" type="button" :disabled="disabled"
      :aria-controls="id" :aria-pressed="visible"
      :aria-label="`${visible?'Sembunyikan':'Tampilkan'} ${toggleLabel}`"
      :title="`${visible?'Sembunyikan':'Tampilkan'} ${toggleLabel}`"
      @click="visible=!visible">
      <AppIcon :name="visible?'eye-off':'eye'" :size="19" />
    </button>
  </div>
</template>
