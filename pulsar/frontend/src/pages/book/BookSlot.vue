<!-- 年鉴素材版位：有素材时显示素材（图片/视频），没有时显示占位框，点击可添加 -->
<template>
  <div class="bslot" :class="[has ? 'has' : 'empty', compact ? 'bslot-compact' : '']">
    <template v-if="has">
      <video v-if="isVideo" class="bslot-media" :src="src" autoplay loop muted playsinline
             @click="toggleVideo($event)"></video>
      <div v-else class="bslot-media bslot-img" :style="{ backgroundImage: 'url(&quot;' + src + '&quot;)' }"
           @click="$emit('view', type)"></div>
      <div class="bslot-cap" v-if="!compact">
        {{ label }}<span v-if="count > 1"> · {{ count }}</span>
      </div>
    </template>
    <div v-else class="bslot-empty" @click="$emit('add', type)">
      <div class="bslot-empty-in">
        <q-icon :name="isVideoType ? 'movie' : 'add_photo_alternate'" :size="compact ? '18px' : '26px'"/>
        <b>{{ label }}</b>
        <span class="bslot-hint" v-if="!compact">{{ hint }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {storeToRefs} from 'pinia'
import {useGlobalStore} from 'src/stores/globalData'

const props = defineProps<{
  type: string
  label: string
  pics: any
  compact?: boolean
}>()
defineEmits(['add', 'view'])

const {lang} = storeToRefs(useGlobalStore())

const list = computed(() => (props.pics && props.pics[props.type]) || [])
const has = computed(() => list.value.length > 0)
const count = computed(() => list.value.length)
const src = computed(() => (has.value ? list.value[0].Path : ''))
const isVideo = computed(() => /\.(mp4|webm|flv|avi|wmv|mkv|mov)$/i.test(src.value) || props.type == 'video')
const isVideoType = computed(() => props.type == 'video')
const hint = computed(() => {
  const v = (lang.value as any).bookClickToAdd
  return v ? v : '点击添加素材'
})

function toggleVideo(e: Event) {
  const v = e.target as HTMLVideoElement
  if (v.paused) {
    v.play()
  } else {
    v.pause()
  }
}
</script>
